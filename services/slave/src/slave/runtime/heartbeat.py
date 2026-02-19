import asyncio
from slave.outbound.master_client import MasterClient
from shared.queue.connection import MQConnection
from shared.utils import logger

class Heartbeat:
    def __init__(self, master_client: MasterClient, worker_id: str | None = None):
        self.master_client = master_client
        self.mq_conn = MQConnection()
        self.worker_id = worker_id
        self.queue_name = f"worker_{worker_id}_queue"

    async def get_tasks_in_queue(self):
        try:
            async with self.mq_conn.channel() as ch:
                res = await ch.declare_queue(self.queue_name, passive=True)
                return res.declaration_result.message_count or 0
        except Exception as e:
            logger.debug(f"Queue {self.queue_name} not found or error: {e}")
            return 0

    async def start_loop(self, stop_event: asyncio.Event):
        logger.info(f"Starting heartbeat loop for worker {self.worker_id}")
        while not stop_event.is_set():
            try:
                tasks_in_queue = await self.get_tasks_in_queue()
                
                status = "busy" if tasks_in_queue > 0 else "idle"
                
                success = self.master_client.send_heartbeat(
                    status=status,
                    tasks_in_queue=tasks_in_queue
                )
                
                if success:
                    logger.info(f"Heartbeat sent for {self.worker_id} (tasks: {tasks_in_queue})")
                else:
                    logger.warning(f"Heartbeat failed for {self.worker_id}")
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                continue

    