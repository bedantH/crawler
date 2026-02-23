import grpc 
import asyncio
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
from shared.cache.redis import get_redis
from urllib.parse import urlparse

def match_base(base_url, url):
    parsed = urlparse(url)
    b_url = f"{parsed.scheme}://{parsed.netloc}"

    return base_url == b_url

async def _handle_crawl_request(urls: list, depth: int, crawl_id: str):
    logger.info(
        "[frontier:grpc] _handle_crawl_request: crawl_id=%s depth=%d urls=%d",
        crawl_id, depth, len(urls),
    )
    async with AsyncSession(engine) as session:
        try:
            crawl_request_query = select(DBCrawlRequest).where(DBCrawlRequest.id == UUID(crawl_id))
            crawl_request = (await session.exec(crawl_request_query)).one()
        except exc.NoResultFound:
            crawl_request = None
        except Exception as e:
            logger.exception("Error occurred when retrieving the crawl_request: %s", e)
            crawl_request = None

    if crawl_request is None:
        logger.error("Crawl Request Not Found")
        return "failed"

    if depth >= crawl_request.max_depth:
        logger.info(
            "Maximum crawl depth reached for %s. Skipping %s discovered URLs.",
            crawl_id, len(urls),
        )
        return "skipped"    

    robots = crawl_request.robots
    rp = RobotsParser(robots=robots)

    allowed_urls = [url for url in urls if rp.can_fetch(url)]
    not_allowed_urls = [url for url in urls if not rp.can_fetch(url)]

    if crawl_request.total_urls_completed + len(allowed_urls) > crawl_request.max_pages:
        remaining = crawl_request.max_pages - crawl_request.total_urls_completed
        allowed_urls = allowed_urls[:remaining]

    if not_allowed_urls:
        logger.info(
            "Following URLs blocked by robots policy: %s", not_allowed_urls
        )

    if not allowed_urls:
        logger.warning("No allowed URLs for crawl_id=%s", crawl_id)
        return "skipped"

    publisher = BasePublisher("crawl_requests")
    redis = get_redis()

    to_queue = []
    for url in allowed_urls:
        visited = await redis.get(f"crawl:visited:{url}")
        if visited is None and match_base(crawl_request.base_url, url):
            to_queue.append(url)

    if not to_queue:
        logger.warning("No allowed URLs for crawl_id=%s", crawl_id)
        return "skipped"

    await redis.incrby(f"crawl:in_flight:{crawl_request.id}", len(to_queue))
    for url in to_queue:
        await publisher.publish("crawl_request", {
            "crawl_id": str(crawl_request.id),
            "base_url": crawl_request.base_url,
            "url": url,
            "depth": depth + 1,
        })
            
    logger.info(
        "[frontier:grpc] ✓ Queued %d/%d URLs for crawl_id=%s depth=%d",
        len(to_queue), len(allowed_urls), crawl_id, depth,
    )
    return "queued"


class CrawlServicer(frontier_pb2_grpc.FrontierServiceServicer):
    @override
    async def CrawlRequest(
        self,
        request: frontier__pb2.FrontierRequest,
        context: grpc.ServicerContext,
    ) -> frontier__pb2.FrontierResponse:
        urls: list = list(request.url)
        depth: int = request.depth
        crawl_id: str = request.crawl_id

        logger.info(
            "[frontier:grpc] ← CrawlRequest: crawl_id=%s depth=%d urls=%d",
            crawl_id, depth, len(urls),
        )

        status = await _handle_crawl_request(urls, depth, crawl_id)
        return frontier__pb2.FrontierResponse(status=status)


async def serve():
    server = grpc.aio.server()
    frontier_pb2_grpc.add_FrontierServiceServicer_to_server(CrawlServicer(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    logger.info("Frontier gRPC server started on port 50051")
    await server.wait_for_termination()
