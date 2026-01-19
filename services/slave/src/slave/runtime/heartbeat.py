import asyncio
from slave.config import WORKER_ID
from slave.outbound.master_client import MasterClient
from shared.queue.connection import MQConnection
from shared.utils import logger

class Heartbeat:
    def __init__(self):
        self.master_client = MasterClient()
        self.mq_conn = MQConnection()
        self.queue_name = f"worker_{WORKER_ID}_queue"

    def get_tasks_in_queue(self):
        try:
            with self.mq_conn.channel() as ch:
                res = ch.queue_declare(queue=self.queue_name, passive=True)
                return res.method.message_count
        except Exception as e:
            logger.debug(f"Queue {self.queue_name} not found or error: {e}")
            return 0

    async def start_loop(self, stop_event: asyncio.Event):
        logger.info(f"Starting heartbeat loop for worker {WORKER_ID}")
        while not stop_event.is_set():
            try:
                tasks_in_queue = self.get_tasks_in_queue()
                
                status = "busy" if tasks_in_queue > 0 else "idle"
                
                success = self.master_client.send_heartbeat(
                    status=status,
                    tasks_in_queue=tasks_in_queue
                )
                
                if success:
                    logger.info(f"Heartbeat sent for {WORKER_ID} (tasks: {tasks_in_queue})")
                else:
                    logger.warning(f"Heartbeat failed for {WORKER_ID}")
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                continue

    