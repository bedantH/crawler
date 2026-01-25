import aio_pika
import json
import asyncio
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from slave.entities.task import Task

class WorkerConsumer(BaseConsumer):
    def __init__(self, exchange_name, queue_name, routing_key, extractor_queue: asyncio.Queue):
        super().__init__(exchange_name, queue_name, routing_key)
        self.extractor_queue = extractor_queue

    async def on_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body)
        logger.info(f"Received message: {data}")
        
        task = Task(
            depth=data.get('depth', 0),
            url=data['url'],
            message=message
        )

        await self.extractor_queue.put(task)
        
        return await message.ack()