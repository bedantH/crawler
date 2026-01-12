import grpc
from frontier.proto.frontier_pb2 import FrontierRequest
from frontier.proto.frontier_pb2_grpc import FrontierServiceStub
from slave.config import WORKER_ID
from shared.utils import logger
import os

class FrontierClient():
  def __init__(self):
    self.frontier_host = os.getenv("FRONTIER_HOST", "localhost")
    self.frontier_port = os.getenv("FRONTIER_PORT", "50051")
    self.channel = grpc.insecure_channel(f"{self.frontier_host}:{self.frontier_port}")
    self.stub = FrontierServiceStub(self.channel)

  def send_crawl_request(self):
    pass
  