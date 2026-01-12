from shared.queue.base_consumer import BaseConsumer
from shared.utils import logger
from master.core.task_dispatcher import TaskDispatcher

class MasterConsumer(BaseConsumer):
    def on_message(self, ch, method, properties, body):
        try:
            import json
            data = json.loads(body)

            dispatcher = TaskDispatcher()
            dispatcher.dispatch(task_data=data)

            logger.info(f" [x] Received {body}") 
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error("Error occurred when handling on_message on MasterConsumer: %s", e)
