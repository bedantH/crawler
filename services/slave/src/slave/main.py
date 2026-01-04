import grpc
from dotenv import load_dotenv
load_dotenv()

import shared.protos.frontier.frontier_pb2 as frontier__pb2
import shared.protos.frontier.frontier_pb2_grpc as frontier_pb2_grpc
from .consume import start_consume

def send_url():
  with grpc.insecure_channel('localhost:50051') as channel:
    stub = frontier_pb2_grpc.FrontierServiceStub(channel)
    request = frontier__pb2.FrontierRequest(url='http://example.com') # type: ignore
    response = stub.Crawl(request)

    print(f'Received response: URL={response.url}, Status={response.status}')

if __name__ == '__main__':
  start_consume()
