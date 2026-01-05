from shared.queue.base_consumer import BaseConsumer
import json
from shared.utils import logger

import time

class MasterConsumer(BaseConsumer):
    def on_message(self, ch, method, properties, body):
        data = json.loads(body)
        logger.info("Processing: %s", data)

        time.sleep(10)
        ch.basic_ack(delivery_tag=method.delivery_tag)