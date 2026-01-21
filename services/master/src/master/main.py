import asyncio
from master.core.heartbeat import Heartbeat
from master.core.consumer import MasterConsumer
from master.core.master_grpc_server import serve
from shared.utils import logger

async def main():
    stop_event = asyncio.Event()

    heartbeat = Heartbeat(stop_event=stop_event)

    logger.info("Starting Master RabbitMQ consumer...")
    consumer = MasterConsumer(
        exchange_name="crawl_requests",
        queue_name="crawl_requests_queue",
        routing_key="crawl_request"
    )

    await asyncio.gather(
        consumer.start(stop_event=stop_event),
        heartbeat.monitor_loop(),
        serve(stop_event=stop_event)
    )

if __name__ == "__main__":
    asyncio.run(main())