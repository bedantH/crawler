import json
from shared.queue.base_publisher import BasePublisher
from shared.utils import logger

async def push_to_deadletter(task_id: str, task_data: dict):
    try:
        publisher = BasePublisher("dead_letter_queue")
        await publisher.publish("dead_letter", {
            "id": task_id,
            "data": json.dumps(task_data)
        })

        logger.info("Item pushed to the dead_letter queue.")

    except Exception as e:
        logger.exception("Error occurred when pushing to the dead-letter queue: %s", e)
        raise