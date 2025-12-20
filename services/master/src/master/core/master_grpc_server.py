from concurrent import futures
import grpc
import master.proto.master_pb2 as master__pb2
import master.proto.master_pb2_grpc as master_pb2_grpc
from typing import override
from shared.utils import logger
from datetime import datetime
import time
from services.master.src.master.infra.db import DBConnection

class MasterServicer(master_pb2_grpc.MasterServiceServicer):
  @override
  def ReportTaskUpdate(self, request: master__pb2.TaskUpdateRequest, context: grpc.ServicerContext):
    try:
      db = DBConnection()
      cursor = db.get_cursor()

      worker_id = request.worker_id
      task_id = request.task_id
      status = request.status

      cursor.execute("""
         SELECT * FROM workers WHERE id = ? AND status != 'failed';        
      """, (worker_id,))

      worker = cursor.fetchone()

      ALLOWED = {'assigned', 'running', 'failed', 'completed', 'rescheduled', 'cancelled'}
      if worker is None or request.status not in ALLOWED:
        return master__pb2.TaskUpdateResponse(acknowledged=False)
      
      now = datetime.now()

      set_keys: list[str] = ['status = ?']
      set_values: list = [status]

      if status == "running":
        set_keys.append('started_at = ?')
        set_values.append(now)

      if status in ('completed', 'cancelled'):
        set_keys.append("finished_at = ?")
        set_values.append(now)

      if worker['status'] == "rescheduled" and status == "running":
        set_keys.append("retries = ?")
        total_retries = worker['retries'] + 1

        set_values.append(total_retries)

      set_clause_str = ", ".join(set_keys)

      update_query = f"""
        UPDATE tasks 
        SET {set_clause_str}
        WHERE task_id = ? AND worker_id = ?
      """

      cursor.execute(update_query, set_values + [task_id, worker_id])

      db.conn.commit()
      db.close_conn()

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

      db = DBConnection()
      cursor = db.get_cursor()

      cursor.execute("""
        SELECT * FROM workers WHERE id = ? AND status != 'failed';
      """, (worker_id,))

      worker = cursor.fetchone()

      if worker == None or status not in ['busy', 'idle', 'shutting_down']:
        return master__pb2.HeartbeatResponse(heartbeat_ack="failed")
      
      total_tasks_completed = worker.get('total_tasks_completed', 0) + tasks_completed
      now = time.time()
      update_query = """
        UPDATE workers
        SET status = ?, 
            last_heartbeat = ?,
            total_tasks_completed = ?,
            tasks_in_queue = ?
        WHERE id = ?
      """
      cursor.execute(update_query, (status, now, total_tasks_completed, tasks_in_queue, worker_id))

      db.conn.commit()
      db.close_conn()

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