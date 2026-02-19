import aio_pika
import json
import asyncio
import shared.database.models
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from slave.entities.task import Task
from slave.entities.worker import Worker

class WorkerConsumer(BaseConsumer):
    def __init__(self, worker: Worker, exchange_name, queue_name, routing_key, fetcher_queue: asyncio.Queue):
        super().__init__(exchange_name, queue_name, routing_key)
        self.fetcher_queue = fetcher_queue
        self.worker = worker

    async def on_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body)
        logger.info(f"Received message: {data}")
    
        try:
            task = Task(
                task_id=data.get('task_id'),
                depth=data.get('depth', 0),
                url=data['url'],
                message=message
            )
            
            # mark the task as assigned
            self.worker.master_client.report_task_update(
                task_id=task.task_id,
                status="assigned"
            )

            await self.fetcher_queue.put(task)
        except Exception as e:
            logger.exception("Error occurred with the payload from Worker Queue. Skipping...")