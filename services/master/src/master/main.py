from master.core.heartbeat import Heartbeat
from master.core.consumer import MasterConsumer

if __name__ == "__main__":
    # Start the heartbeat loop
    heartbeat = Heartbeat()
    heartbeat.init()

    # setup consumer
    consumer = MasterConsumer(
        exchange_name="crawl_requests",
        queue_name="crawl_requests_queue",
        routing_key="crawl_request"
    )

    consumer.start()