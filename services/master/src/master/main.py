import threading
from master.core.heartbeat import Heartbeat
from master.core.consumer import MasterConsumer
from master.core.master_grpc_server import serve
from shared.utils import logger

if __name__ == "__main__":
    # 1. Start the dead-worker monitor loop (internal thread)
    heartbeat = Heartbeat()
    heartbeat.init()

    # 2. Start the gRPC server in a separate thread
    logger.info("Starting Master gRPC server thread...")
    grpc_thread = threading.Thread(target=serve, daemon=True)
    grpc_thread.start()

    # 3. Start the main RabbitMQ consumer (blocking)
    logger.info("Starting Master RabbitMQ consumer...")
    consumer = MasterConsumer(
        exchange_name="crawl_requests",
        queue_name="crawl_requests_queue",
        routing_key="crawl_request"
    )

    try:
        consumer.start()
    except KeyboardInterrupt:
        logger.info("Master service shutting down...")