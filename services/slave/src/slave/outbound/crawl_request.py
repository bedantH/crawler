import grpc
import grpc.aio
import shared.protos.frontier.frontier_pb2 as frontier_pb2
from shared.protos.frontier.frontier_pb2_grpc import FrontierServiceStub
from shared.utils import logger
import os


class FrontierClient:
    def __init__(self):
        self.frontier_host = os.getenv("FRONTIER_HOST", "localhost")
        self.frontier_port = os.getenv("FRONTIER_PORT", "50051")
        # aio channel required for async stub calls
        self.channel = grpc.aio.insecure_channel(f"{self.frontier_host}:{self.frontier_port}")
        self.stub = FrontierServiceStub(self.channel)

    async def send_crawl_request(self, url: list[str], depth: int, crawl_id: str):
        try:
            request = frontier_pb2.FrontierRequest(
                url=url,
                depth=depth,
                crawl_id=crawl_id,
            )
            logger.info(
                "[worker:frontier_client] → Sending %d URLs to frontier depth=%d crawl_id=%s",
                len(url), depth, crawl_id,
            )
            response = await self.stub.CrawlRequest(request)
            logger.info("[worker:frontier_client] ✓ Frontier replied: status=%s", response.status)
            return {"status": response.status}

        except Exception as e:
            logger.error("[worker:frontier_client] ✗ Failed to send crawl request: %s", e)
            return None
