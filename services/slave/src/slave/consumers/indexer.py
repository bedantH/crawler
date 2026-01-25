import asyncio
from shared.utils import logger
from slave.entities.worker import Worker

async def indexer_worker(worker: Worker, stop_event: asyncio.Event):
    logger.info("Indexer worker started")
    while not stop_event.is_set():
        try:
            task = await asyncio.wait_for(worker.indexer_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        try:
            logger.info(f"Indexer processing task: {task.get('url')}")
            
            # Simulate work (0.2s)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=0.2)
                break
            except asyncio.TimeoutError:
                pass
            
            logger.info(f"Successfully processed and indexed task: {task.get('url')}")
        except Exception as e:
            logger.error(f"Indexer failed for task {task}: {e}")
        finally:
            worker.indexer_queue.task_done()
    logger.info("Indexer worker shutting down")
