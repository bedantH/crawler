import asyncio
from shared.utils import logger
import asyncio
from slave.entities.task import Task
from slave.entities.worker import Worker

async def extractor_worker(worker: Worker, stop_event: asyncio.Event):
    logger.info("Extractor worker started")
    while not stop_event.is_set():
        try:
            task: Task = await asyncio.wait_for(worker.extractor_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        try:
            logger.info(f"Extractor processing task: {task.url}")
            
            # Simulate work (1s) but be interruptible by stop_event
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=1.0)
                # If we get here, stop_event was SET. Stop processing.
                break
            except asyncio.TimeoutError:
                # Timeout happened, which means 1.0s passed and stop_event was NOT set.
                # Work simulation done.
                pass

            await worker.send_to_parser(task)
        except Exception as e:
            logger.error(f"Extractor failed for task {task}: {e}")
        finally:
            worker.extractor_queue.task_done()
    logger.info("Extractor worker shutting down")