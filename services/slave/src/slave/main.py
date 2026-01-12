import asyncio
from dotenv import load_dotenv
from slave.config import WORKER_ID
from slave.runtime.consumer import WorkerConsumer
from slave.runtime.heartbeat import Heartbeat
from shared.utils import logger

load_dotenv()

async def main():
    stop_event = asyncio.Event()
    
    # Start consuming messages from the queue
    consumer = WorkerConsumer(
        exchange_name=f"worker_{WORKER_ID}",
        queue_name=f"worker_{WORKER_ID}_queue",
        routing_key=f"worker_{WORKER_ID}_task",
    )

    heartbeat = Heartbeat()

    logger.info(f"Worker {WORKER_ID} starting...")
    
    await asyncio.gather(
        consumer.start_consume(stop_event=stop_event),
        heartbeat.start_loop(stop_event=stop_event)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
