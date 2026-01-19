import json
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
import time
import asyncio

class WorkerConsumer(BaseConsumer):
    async def on_message(self, ch, method, properties, body):
        data = json.loads(body)
        logger.info(f"Received message: {data}")
        
        await asyncio.sleep(10)
        return ch.basic_ack(delivery_tag=method.delivery_tag)
    
    async def start_consume(self, stop_event: asyncio.Event):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.start, stop_event)