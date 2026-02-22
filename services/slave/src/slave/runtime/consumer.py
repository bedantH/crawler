import aio_pika
import json
import asyncio
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from slave.entities.task import Task
from slave.entities.worker import Worker


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

    async def on_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body)

        logger.info("[worker:consumer] ← Received task: task_id=%s url=%s depth=%s",
                    data.get("task_id"), data.get("url"), data.get("depth"))

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
                task_id=task.task_id, status="assigned"
            )

            logger.info("[worker:consumer] → Enqueuing task_id=%s to fetcher queue", task.task_id)
            await self.fetcher_queue.put(task)

        except Exception as e:
            logger.exception(
                "[worker:consumer] ✗ Error processing payload for task_id=%s — skipping",
                data.get("task_id"),
            )
