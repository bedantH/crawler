import aio_pika
import json
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
import time

class WorkerConsumer(BaseConsumer):
    def on_message(self, message: aio_pika.IncomingMessage):
        data = json.loads(message.body)
        logger.info(f"Received message: {data}")
        
        time.sleep(10)
        return message.ack()