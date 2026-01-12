import grpc
import master.proto.master_pb2 as master_pb2
import master.proto.master_pb2_grpc as master_pb2_grpc
from slave.config import WORKER_ID
from shared.utils import logger
import os

class MasterClient:
    def __init__(self):
        self.master_host = os.getenv("MASTER_HOST", "localhost")
        self.master_port = os.getenv("MASTER_PORT", "50052")
        self.channel = grpc.insecure_channel(f"{self.master_host}:{self.master_port}")
        self.stub = master_pb2_grpc.MasterServiceStub(self.channel)

    def send_heartbeat(self, status: str = "idle", tasks_in_queue: int = 0):
        try:
            request = master_pb2.HeartbeatRequest(
                worker_id=WORKER_ID,
                status=status,
                tasks_in_queue=tasks_in_queue
            )
            response = self.stub.HandleHeartbeat(request)
            return response.heartbeat_ack == "success"
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False

    def report_task_update(self, task_id: str, status: str):
        try:
            request = master_pb2.TaskUpdateRequest(
                worker_id=WORKER_ID,
                task_id=task_id,
                status=status
            )
            response = self.stub.ReportTaskUpdate(request)
            return response.acknowledged
        except Exception as e:
            logger.error(f"Failed to report task update: {e}")
            return False
