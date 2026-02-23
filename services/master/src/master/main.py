import asyncio
import signal
from master.core.heartbeat import Heartbeat
from master.core.consumer import MasterConsumer
from master.core.master_grpc_server import serve
from shared.utils import logger
from shared.database.setup_db import create_db_tables
from shared.cache.redis import init_redis, close_redis
from shared.config import REDIS_HOST


async def main():
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received shutdown signal, stopping...")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    logger.info("Creating database tables...")
    await create_db_tables()

    logger.info("Connecting to Redis...")
    await init_redis(host=REDIS_HOST)

    heartbeat = Heartbeat(stop_event=stop_event)

    logger.info("Starting Master RabbitMQ consumer...")
    consumer = MasterConsumer(
        exchange_name="crawl_requests",
        queue_name="crawl_requests_queue",
        routing_key="crawl_request",
    )

    logger.info("Starting all master tasks (consumer, heartbeat, gRPC server)...")
    try:
        await asyncio.gather(
            consumer.start(stop_event=stop_event),
            heartbeat.monitor_loop(),
            serve(stop_event=stop_event),
        )
    finally:
        await close_redis()


if __name__ == "__main__":
    asyncio.run(main())

