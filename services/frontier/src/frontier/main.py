from fastapi import FastAPI, HTTPException, Request
from sqlmodel import select
from sqlalchemy import exc
from shared.database.models.crawl_requests import CrawlRequest, CrawlStatus
from sqlmodel.ext.asyncio.session import AsyncSession
from shared.database.setup_db import create_db_tables
import aiohttp

from shared.database.engine import engine
from shared.queue.base_publisher import BasePublisher
from .dto.crawl import CrawlRequest as CrawlRequestDTO
from .frontier_grpc_server import serve 
from contextlib import asynccontextmanager
from shared.utils import logger
from urllib.parse import urlparse
from shared.cache.redis import RedisClient
from shared.config import REDIS_HOST

import asyncio

_grpc_server_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
  await create_db_tables()
  
  # run grpc server natively in the event loop along with FastAPI
  global _grpc_server_task
  _grpc_server_task = asyncio.create_task(serve())
  
  logger.info("Frontier service started")
  logger.info("Frontier service started")
  
  try:
    yield
  finally:
    logger.info("Frontier service stopped")

app = FastAPI(
  title="Frontier Service",
  description="A service for managing web crawling tasks",
  version="1.0.0",
  lifespan=lifespan
)

@app.get("/health-check")
def health_check():
    return {"status": "ok"}
    
@app.post('/crawl')
async def crawl(request: Request, crawl_request: CrawlRequestDTO):
  try:
    url = crawl_request.url
    depth: int = crawl_request.depth
    max_pages = crawl_request.max_pages
    
    # find crawl request by url
    async with AsyncSession(engine) as session:
      try:
        select_crawl_req_query = select(CrawlRequest).where(CrawlRequest.seed_url == url)
        existing_crawl_request = (await session.exec(select_crawl_req_query)).one()
      except exc.NoResultFound:
        existing_crawl_request = None

    if existing_crawl_request:
      raise HTTPException(status_code=409, detail="Crawl request already exists", headers={
        "Location": f"/crawl/status/{existing_crawl_request.id}"
      })
    
    if not url.startswith(("http://", "https://")):
      url = "https://" + url

    parsed = urlparse(url)
    host = parsed.netloc
    scheme = parsed.scheme

    base_url = f"{scheme}://{host}"

    # fetch the robots.txt
    robots_text = ""
    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(f"{base_url}/robots.txt", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    robots_text = await response.text()
    except Exception:
        robots_text = ""

    # create crawl request
    crawl_request_mo = CrawlRequest(
      seed_url=url.strip(),
      base_url=base_url,
      max_depth=depth,
      max_pages=max_pages,
      status=CrawlStatus.PENDING,
      robots=robots_text
    )

    async with AsyncSession(engine) as session:
      try:
        session.add(crawl_request_mo)
        await session.commit()
        # refresh crawl_request_mo to get id later
        await session.refresh(crawl_request_mo)

      except exc.DuplicateColumnError as e:
        logger.error("Duplicate Column: %s", e, exc_info=True)
        raise HTTPException(status_code=409, detail="Crawl Request already Exists")
      except Exception as e:
        logger.error("Failed to insert crawl request: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to insert crawl request")

    logger.info(f"Created crawl request with ID: {crawl_request_mo.id}")
    
    try:  
      logger.info("Sending crawl request to queue")

      publisher = BasePublisher("crawl_requests")
      crawl_body = crawl_request_mo.model_dump(mode="json")

      await publisher.publish("crawl_request", {
        "crawl_id": str(crawl_request_mo.id),
        "base_url": crawl_request_mo.base_url,
        "url": crawl_request_mo.seed_url,
        "depth": 0
      })

      client = RedisClient(host=REDIS_HOST)

      # set crawl request id in redis to 1 as an Inflight counter
      client.set(f"crawl:in_flight:{crawl_request_mo.id}", 1)

      logger.info(f"Crawl request {crawl_request_mo.id} sent to queue")
      return crawl_body
    except Exception as e:
      logger.error("Failed to publish crawl request: %s", e, exc_info=True)

  except Exception as e:
    logger.error("Internal Server Error: %s", e, exc_info=True)
    raise HTTPException(status_code=500, detail="Internal Server Error")
  