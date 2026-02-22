import asyncio
import aiohttp
from shared.utils import logger
from slave.entities.worker import Worker
from slave.entities.task import Task


async def fetch_worker(worker: Worker, stop_event: asyncio.Event):
    logger.info("[worker:fetcher] Fetcher worker started")
    while not stop_event.is_set():
        try:
            task: Task = await asyncio.wait_for(worker.fetch_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        logger.info("[worker:fetcher] ← Got task_id=%s url=%s", task.task_id, task.url)

        await worker.master_client.report_task_update(
            task_id=task.task_id, status="running"
        )
        logger.info("[worker:fetcher] → Reported 'running' to master for task_id=%s", task.task_id)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(task.url) as response:
                    content = await response.text()
                    task.raw_html = content
                    logger.info("[worker:fetcher] ✓ Fetched url=%s status=%s size=%d bytes",
                                task.url, response.status, len(content))

            logger.info("[worker:fetcher] → Sending task_id=%s to parser queue", task.task_id)
            await worker.send_to_parser(task)

        except Exception as e:
            logger.error("[worker:fetcher] ✗ Fetch failed for task_id=%s url=%s — %s",
                         task.task_id, task.url, e)
            await worker.master_client.report_task_update(
                task_id=task.task_id, status="failed"
            )
            await task.message.nack(requeue=False)
        finally:
            worker.fetch_queue.task_done()

    logger.info("[worker:fetcher] Fetcher worker shutting down")
