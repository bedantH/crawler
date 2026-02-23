import aio_pika
import json
import asyncio
import time
from typing import override
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from shared.config import CONSUMER_INACTIVITY_TIMEOUT
from slave.entities.task import Task
from slave.entities.worker import Worker
from shared.database.models.worker import WorkerStatus 


class WorkerConsumer(BaseConsumer):
    def __init__(
        self,
        worker: Worker,
        exchange_name,
        queue_name,
        routing_key,
        fetcher_queue: asyncio.Queue,
    ):
        super().__init__(exchange_name, queue_name, routing_key)
        self.fetcher_queue = fetcher_queue
        self.worker = worker
        self.last_activity = time.time()

    async def on_message(self, message: aio_pika.IncomingMessage):
        self.last_activity = time.time()
        data = json.loads(message.body)

        logger.info("[worker:consumer] ← Received task: task_id=%s url=%s depth=%s",
                    data.get("task_id"), data.get("url"), data.get("depth"))
        
        # update the worker entity status to busy
        self.worker.status = WorkerStatus.BUSY

        try:
            task = Task(
                task_id=data["task_id"],
                depth=data.get("depth", 0),
                url=data["url"],
                base_url=data["base_url"],
                crawl_id=data["crawl_id"],
                message=message,
            )

            logger.info("[worker:consumer] → Reporting 'assigned' to master for task_id=%s", task.task_id)
            await self.worker.master_client.report_task_update(
                task_id=task.task_id, status="assigned", crawl_id=task.crawl_id
            )

            logger.info("[worker:consumer] → Enqueuing task_id=%s to fetcher queue", task.task_id)
            await self.fetcher_queue.put(task)

        except Exception as e:
            logger.exception(
                "[worker:consumer] ✗ Error processing payload for task_id=%s — skipping",
                data.get("task_id"),
            )

    async def _inactivity_monitor(self, stop_event: asyncio.Event):
        logger.info("[worker:consumer] Inactivity monitor started (timeout=%ds)", CONSUMER_INACTIVITY_TIMEOUT)
        while not stop_event.is_set():
            await asyncio.sleep(5)
            elapsed = time.time() - self.last_activity
            if elapsed >= CONSUMER_INACTIVITY_TIMEOUT:
                logger.warning(
                    "[worker:consumer] No messages received for %d seconds. Terminating worker...",
                    CONSUMER_INACTIVITY_TIMEOUT
                )
                self.worker.status = WorkerStatus.SHUTTING_DOWN
                stop_event.set()
                break

    @override
    async def start(self, stop_event: asyncio.Event):
        logger.info("[worker:consumer] Starting consumer for queue %s", self.queue_name)
        # start the inactivity monitor as a background task
        monitor_task = asyncio.create_task(self._inactivity_monitor(stop_event))
        
        try:
            await super().start(stop_event)
        finally:
            # cancel the monitor_task, if the super().start() call resolves for some reason (its supposed to be blocking)
            monitor_task.cancel()
            # doesn't cancel automatically, need to invoke again to get the CancelledError to identify it was cancelled
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass