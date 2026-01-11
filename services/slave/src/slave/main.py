import shared.protos.frontier.frontier_pb2 as frontier__pb2
import shared.protos.frontier.frontier_pb2_grpc as frontier_pb2_grpc
from slave.config import WORKER_ID
from slave.runtime.consumer import WorkerConsumer
import asyncio

import grpc
from dotenv import load_dotenv
load_dotenv()

def send_url():
  with grpc.insecure_channel('localhost:50051') as channel:
    stub = frontier_pb2_grpc.FrontierServiceStub(channel)
    request = frontier__pb2.FrontierRequest(url='http://example.com') # type: ignore
    response = stub.Crawl(request)

    print(f'Received response: URL={response.url}, Status={response.status}')

if __name__ == '__main__':
    # stop_event

    stop_event = asyncio.Event()

    # Start consuming messages from the queue
    consumer = WorkerConsumer(
        exchange_name=f"worker_{WORKER_ID}",
        queue_name=f"worker_{WORKER_ID}_queue",
        routing_key=f"worker_{WORKER_ID}_task",
    )

    tasks = [
      consumer.start_consume(stop_event=stop_event),
    ]
  


