import asyncio
from shared.database.models.worker import WorkerStatus
from slave.entities.task import Task
from slave.outbound.master_client import MasterClient

class Worker:
    def __init__(self, master_client: MasterClient, worker_id: str | None = None):
        self.master_client = master_client
        self.worker_id = worker_id
        self.status = WorkerStatus.IDLE
        
        self.fetch_queue = asyncio.Queue(maxsize=30)
        self.parser_queue = asyncio.Queue(maxsize=30)
        self.indexer_queue = asyncio.Queue(maxsize=30)
        # self.extractor_queue = asyncio.Queue(maxsize=30)

    async def send_to_parser(self, task: Task):
        await self.parser_queue.put(task)

    async def send_to_indexer(self, task: Task):
        await self.indexer_queue.put(task)

    # async def send_to_extractor(self, task: Task):
    #     await self.extractor_queue.put(task)
