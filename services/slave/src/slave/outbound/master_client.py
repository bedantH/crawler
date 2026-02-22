import grpc
import shared.protos.master.master_pb2 as master_pb2
import shared.protos.master.master_pb2_grpc as master_pb2_grpc
from slave.config import WORKER_ID
from shared.utils import logger
import os
from shared.protos.master.master_pb2_grpc import MasterServiceStub

# States that indicate the channel is recoverable without reconnect
_HEALTHY_STATES = {
    grpc.ChannelConnectivity.IDLE,
    grpc.ChannelConnectivity.CONNECTING,
    grpc.ChannelConnectivity.READY,
}

class MasterClient:
    def __init__(self):
        self.master_host = os.getenv("MASTER_HOST", "localhost")
        self.master_port = os.getenv("MASTER_PORT", "50052")
        self._channel = None
        self._stub: MasterServiceStub | None = None

    async def _get_channel(self):
        # Only recreate if channel is missing or in a terminal failure state
        if self._channel is None or self._channel.get_state() not in _HEALTHY_STATES:
            if self._channel:
                try:
                    await self._channel.close()
                except Exception:
                    pass
            self._channel = grpc.aio.insecure_channel(
                f"{self.master_host}:{self.master_port}"
            )
            self._stub = master_pb2_grpc.MasterServiceStub(self._channel)
        return self._channel

    async def send_heartbeat(self, status: str = "idle", tasks_in_queue: int = 0):
        try:
            request = master_pb2.HeartbeatRequest(
                worker_id=WORKER_ID, status=status, tasks_in_queue=tasks_in_queue
            )
            stub = await self._get_stub()
            if stub is not None:
                response = await stub.HandleHeartbeat(request)
                return response.heartbeat_ack == "success"
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            await self._reset_channel()
            return False

    async def report_task_update(self, task_id: str, status: str):
        try:
            request = master_pb2.TaskUpdateRequest(
                worker_id=WORKER_ID, task_id=task_id, status=status
            )
            stub = await self._get_stub()
            if stub is not None:
                response = await stub.ReportTaskUpdate(request)
                return response.acknowledged
        except Exception as e:
            logger.error(f"Failed to report task update: {e}")
            await self._reset_channel()
            return False

    async def _get_stub(self) -> MasterServiceStub | None:
        if self._stub is None:
            await self._get_channel()
        return self._stub

    async def _reset_channel(self):
        if self._channel:
            try:
                await self._channel.close()
            except Exception:
                pass
        self._channel = None
        self._stub = None
