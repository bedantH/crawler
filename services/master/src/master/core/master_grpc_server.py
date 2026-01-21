import asyncio
import grpc
import master.proto.master_pb2 as master__pb2
import master.proto.master_pb2_grpc as master_pb2_grpc
from shared.database.models.worker import Worker
from shared.database.models.task import Task
from typing import override
from shared.utils import logger
from datetime import datetime

from shared.database.engine import engine
from sqlmodel import select, update, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any

class MasterServicer(master_pb2_grpc.MasterServiceServicer):
  def __init__(self):
    self._semaphore = asyncio.Semaphore(10)

  @override
  async def ReportTaskUpdate(self, request: master__pb2.TaskUpdateRequest, context: grpc.aio.ServicerContext):
    async with self._semaphore:
      try:
        worker_id = request.worker_id
        task_id = request.task_id
        status = request.status

        async with AsyncSession(engine) as session:
          select_worker_st = select(Worker).where(
            (Worker.id == worker_id) & (Worker.status != 'failed')
          )
          worker = (await session.exec(select_worker_st)).first()

          select_task_st = select(Task).where(
            (Task.id == task_id) & (Task.worker_id == worker_id)
          )

          task = (await session.exec(select_task_st)).first()

        ALLOWED = {'assigned', 'running', 'failed', 'completed', 'rescheduled', 'cancelled'}
        if worker is None or request.status not in ALLOWED or task is None:
          return master__pb2.TaskUpdateResponse(acknowledged=False)
        
        now = datetime.utcnow()

        update_data: dict[str, Any] = {
          'status': status
        }

        worker_update_data = {}

        if status == "running":
          update_data['started_at'] = now

        if status in ('completed', 'cancelled'):
          if status == "completed":
            worker_update_data['total_tasks_completed'] = worker.total_tasks_completed + 1

          update_data['finished_at'] = now

        if worker.status == "rescheduled" and status == "running":
          update_data['retries'] = task.retries + 1

        async with AsyncSession(engine) as session:
          update_worker_st = (
            update(Task)
            .where(Task.id == task_id) # type: ignore
            .where(Task.worker_id == worker_id) # type: ignore
            .values(**update_data)
          )

          await session.exec(update_worker_st)
          await session.commit()

        return master__pb2.TaskUpdateResponse(acknowledged=True)

      except Exception as e:
        logger.error("Error occurred when receiving task update from request: %s, %s", request, e, exc_info=True)
        return master__pb2.TaskUpdateResponse(acknowledged=False)

  @override
  async def HandleHeartbeat(self, request: master__pb2.HeartbeatRequest, context: grpc.aio.ServicerContext): # pyright: ignore[reportAttributeAccessIssue]
    async with self._semaphore:
      try:
        worker_id = request.worker_id
        status = request.status
        tasks_in_queue = request.tasks_in_queue

        async with AsyncSession(engine) as session:
          select_worker_st = select(Worker).where(
            (Worker.id == worker_id) & (Worker.status != 'failed')
          )
          worker = (await session.exec(select_worker_st)).first()
        if worker == None or status not in ['busy', 'idle', 'shutting_down']:
          return master__pb2.HeartbeatResponse(heartbeat_ack="failed")

        async with AsyncSession(engine) as session:
          update_query = update(Worker).where(Worker.id == worker_id).values( # type: ignore
            status=status,
            last_heartbeat=datetime.utcnow(),
            tasks_in_queue=tasks_in_queue
          )

          await session.exec(update_query)
          await session.commit()

        return master__pb2.HeartbeatResponse(heartbeat_ack="success")
      except Exception as e:
        logger.error("Error occurred while handling heartbeat from %s: %s", request, e, exc_info=True)
        return master__pb2.HeartbeatResponse(heartbeat_ack="failed")

async def serve(stop_event: asyncio.Event):
  server = grpc.aio.server()
  master_pb2_grpc.add_MasterServiceServicer_to_server(
    MasterServicer(), 
    server
  )
  
  server.add_insecure_port('[::]:50052')
  await server.start()

  logger.info("Master gRPC server started on port 50052")

  await stop_event.wait()

  logger.info("Stopping Master gRPC server...")
  await server.stop(grace=None)
  logger.info("Master gRPC server stopped.")