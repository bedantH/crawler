from concurrent import futures
import grpc
import master.proto.master_pb2 as master__pb2
import master.proto.master_pb2_grpc as master_pb2_grpc
from shared.database.models.worker import Worker
from shared.database.models.task import Task
from typing import override
from shared.utils import logger
from datetime import datetime
import time
from shared.database.engine import engine
from sqlmodel import Session, select, update

class MasterServicer(master_pb2_grpc.MasterServiceServicer):
  @override
  def ReportTaskUpdate(self, request: master__pb2.TaskUpdateRequest, context: grpc.ServicerContext):
    try:
      worker_id = request.worker_id
      task_id = request.task_id
      status = request.status

      with Session(engine) as session:
        select_worker_st = select(Worker).where(
          (Worker.id == worker_id) & (Worker.status != 'failed')
        )
        worker = session.exec(select_worker_st).first()

      ALLOWED = {'assigned', 'running', 'failed', 'completed', 'rescheduled', 'cancelled'}
      if worker is None or request.status not in ALLOWED:
        return master__pb2.TaskUpdateResponse(acknowledged=False)
      
      now = datetime.now()

      update_data = {
        'status': status
      }

      if status == "running":
        update_data['started_at'] = now

      if status in ('completed', 'cancelled'):
        update_data['finished_at'] = now

      if worker['status'] == "rescheduled" and status == "running":
        update_data['retries'] = worker['retries'] + 1

      with Session(engine) as session:
        update_worker_st = update(Task).where((Task.id == task_id) & (Task.worker_id == worker_id)).values(
          **update_data          
        )

        session.exec(update_worker_st)
        session.commit()

      return master__pb2.TaskUpdateResponse(acknowledged=True)

    except Exception as e:
      logger.error("Error occurred when receiving task update from request: %s, %s", request, e, exc_info=True)
      return master__pb2.TaskUpdateResponse(acknowledged=False)

  @override
  def HandleHeartbeat(self, request: master__pb2.HeartbeatRequest, context: grpc.ServicerContext): # pyright: ignore[reportAttributeAccessIssue]
    try:
      worker_id = request.worker_id
      status = request.status
      tasks_completed = request.tasks_completed
      tasks_in_queue = request.tasks_in_queue

      with Session(engine) as session:
        select_worker_st = select(Worker).where(
          (Worker.id == worker_id) & (Worker.status != 'failed')
        )
        worker = session.exec(select_worker_st).first()

      if worker == None or status not in ['busy', 'idle', 'shutting_down']:
        return master__pb2.HeartbeatResponse(heartbeat_ack="failed")
      
      total_tasks_completed = worker.total_tasks_completed + tasks_completed
      now = time.time()

      with Session(engine) as session:
        update_query = update(Worker).where(Worker.id == worker_id).values(
          status=status,
          last_heartbeat=datetime.fromtimestamp(now),
          total_tasks_completed=total_tasks_completed,
          tasks_in_queue=tasks_in_queue
        )

        session.exec(update_query)
        session.commit()
        
      return master__pb2.HeartbeatResponse(heartbeat_ack="success")
    except Exception as e:
      logger.error("Error occurred while handling heartbeat from %s: %s", request, e, exc_info=True)
      return master__pb2.HeartbeatResponse(heartbeat_ack="failed")

def serve():
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
  master_pb2_grpc.add_MasterServiceServicer_to_server(
    MasterServicer(), server
  )
  
  server.add_insecure_port('[::]:50052')
  server.start()

  logger.info("Master gRPC server started on port 50052")

  server.wait_for_termination()