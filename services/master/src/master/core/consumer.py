import aio_pika
import json
from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from master.core.task_dispatcher import TaskDispatcher

class MasterConsumer(BaseConsumer):
    async def on_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            body = message.body
            data = json.loads(body)

            logger.info("[master:consumer] ← Received crawl request: url=%s depth=%s crawl_id=%s",
                        data.get("url"), data.get("depth"), data.get("crawl_id"))

            dispatcher = TaskDispatcher()
            await dispatcher.dispatch(task_data=data)

            logger.info("[master:consumer] ✓ Dispatched task for url=%s", data.get("url"))