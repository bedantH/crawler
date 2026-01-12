import asyncio
import grpc
from dotenv import load_dotenv
from slave.config import WORKER_ID
from slave.runtime.consumer import WorkerConsumer
from slave.outbound.master_client import MasterClient
from shared.utils import logger

load_dotenv()

async def heartbeat_loop(stop_event: asyncio.Event):
    client = MasterClient()
    logger.info(f"Starting heartbeat loop for worker {WORKER_ID}")
    while not stop_event.is_set():
        try:
            success = client.send_heartbeat(status="idle", tasks_in_queue=0)
            if success:
                logger.info(f"Heartbeat sent for {WORKER_ID}")
            else:
                logger.warning(f"Heartbeat failed for {WORKER_ID}")
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")
        
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            continue

async def main():
    stop_event = asyncio.Event()
    
    # Start consuming messages from the queue
    consumer = WorkerConsumer(
        exchange_name=f"worker_{WORKER_ID}",
        queue_name=f"worker_{WORKER_ID}_queue",
        routing_key=f"worker_{WORKER_ID}_task",
    )

    logger.info(f"Worker {WORKER_ID} starting...")
    
    await asyncio.gather(
        consumer.start_consume(stop_event=stop_event),
        heartbeat_loop(stop_event=stop_event)
    )

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
