import grpc 
from shared.database.engine import engine
import shared.protos.frontier.frontier_pb2 as frontier__pb2
import shared.protos.frontier.frontier_pb2_grpc as frontier_pb2_grpc
from sqlmodel import select
from sqlalchemy import exc
from sqlmodel.ext.asyncio.session import AsyncSession
from shared.database.models.crawl_requests import CrawlRequest as DBCrawlRequest
from typing import override
from concurrent import futures
from shared.utils import logger
from uuid import UUID
from frontier.lib.verify import RobotsParser
from shared.queue.base_publisher import BasePublisher
from shared.cache.redis import RedisClient
from shared.config import REDIS_HOST

class CrawlServicer(frontier_pb2_grpc.FrontierServiceServicer):
    @override
    async def CrawlRequest(self, request: frontier__pb2.FrontierRequest, context: grpc.ServicerContext) -> frontier__pb2.FrontierResponse: # pyright: ignore[reportAttributeAccessIssue]
        # Rest will be handled by the worker master when it reads the crawl request from the queue
        urls: list = list(request.url)
        depth: int = request.depth
        crawl_id: str = request.crawl_id

        async with AsyncSession(engine) as session:
            try:
                crawl_request_query = select(DBCrawlRequest).where(DBCrawlRequest.id == UUID(crawl_id))
                crawl_request = (await session.exec(crawl_request_query)).one()
            except exc.NoResultFound:
                crawl_request = None
            except Exception as e:
                logger.exception("Error occurred when retrieving the crawl_request: %s", e)
                crawl_request = None

        if crawl_request == None:
            logger.error("Crawl Request Not Found")
            return frontier__pb2.FrontierResponse(status="failed")
        
        # Check against maximum depth specified by the user
        if depth >= crawl_request.max_depth:
            logger.info("Maximum crawl depth reached for %s. Skipping %s discovered URLs.", crawl_id, len(urls))
            return frontier__pb2.FrontierResponse(status="skipped")

        robots = crawl_request.robots
        rp = RobotsParser(robots=robots)

        allowed_urls = []
        not_allowed_urls = []
        
        for url in urls:
            if rp.can_fetch(url):
                allowed_urls.append(url)
            else:
                not_allowed_urls.append(url)

        if len(not_allowed_urls) > 0:
            logger.info("Following URLs cannot be crawled, because rejected by the robots policy: %s", not_allowed_urls)

        if len(allowed_urls) > 0:
            publisher = BasePublisher("crawl_requests")
            client = RedisClient(host=REDIS_HOST)

            for url in allowed_urls:
                if client.get(url) == None:
                    await publisher.publish("crawl_request", {
                        "crawl_id": str(crawl_request.id),
                        "base_url": crawl_request.base_url,
                        "url": url,
                        "depth": depth + 1 # increment depth for child links
                    })

            print(f"Received crawl request for URL: {request.url} and {request.depth} depth")
            return frontier__pb2.FrontierResponse(status="queued")
        else:
            logger.error("No allowed URLs found for the crawl request")
            return frontier__pb2.FrontierResponse(status="skipped")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    frontier_pb2_grpc.add_FrontierServiceServicer_to_server(CrawlServicer(), server)

    server.add_insecure_port('[::]:50051')
    server.start()
    
    print("Frontier gRPC server started on port 50051")

    server.wait_for_termination()
