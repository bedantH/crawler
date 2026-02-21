import asyncio
import aiohttp
from slave.entities.worker import Worker
from slave.entities.task import Task


async def fetch_worker(worker: Worker, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            task: Task = await asyncio.wait_for(worker.fetch_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        await worker.master_client.report_task_update(
            task_id=task.task_id, status="running"
        )

        try:
            url = task.url
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.text()
                    task.raw_html = content

            await worker.send_to_parser(task)
        except Exception as e:
            print(f"Fetch failed for task {task}: {e}")
            await worker.master_client.report_task_update(
                task_id=task.task_id, status="failed"
            )
            task.message.nack(requeue=False)
        finally:
            worker.fetch_queue.task_done()
