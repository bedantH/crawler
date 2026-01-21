import asyncio
from signal import signal
from dotenv import load_dotenv
from slave.config import WORKER_ID
from slave.runtime.consumer import WorkerConsumer
from slave.runtime.heartbeat import Heartbeat
from shared.utils import logger
from slave.entities.worker import Worker

load_dotenv()

async def main():
    stop_event = asyncio.Event()
    
    worker = Worker(
        worker_id=WORKER_ID
    )
    
    consumer = WorkerConsumer(
        exchange_name=f"worker_{WORKER_ID}",
        queue_name=f"worker_{WORKER_ID}_queue",
        routing_key=f"worker_{WORKER_ID}_task",
    )

    heartbeat = Heartbeat(worker_id=worker.worker_id)

    logger.info(f"Worker {WORKER_ID} starting...")
    
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, stop_event.set)

    await asyncio.gather(
        consumer.start(stop_event=stop_event),
        heartbeat.start_loop(stop_event=stop_event)
    )

if __name__ == '__main__':
    asyncio.run(main())
