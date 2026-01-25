import asyncio
from shared.database.models.worker import WorkerStatus
from slave.entities.task import Task

class Worker:
    def __init__(self, worker_id: str | None = None):
        self.worker_id = worker_id
        self.status = WorkerStatus.IDLE
        
        self.fetch_queue = asyncio.Queue(maxsize=30)
        self.parser_queue = asyncio.Queue(maxsize=30)
        self.extractor_queue = asyncio.Queue(maxsize=30)
        self.indexer_queue = asyncio.Queue(maxsize=30)

    async def send_to_parser(self, task: Task):
        await self.parser_queue.put(task)

    async def send_to_extractor(self, task: Task):
        await self.extractor_queue.put(task)

    async def send_to_indexer(self, task: Task):
        await self.indexer_queue.put(task)
