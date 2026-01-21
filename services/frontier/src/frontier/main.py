from fastapi import FastAPI, HTTPException, Request
from sqlmodel import select
from sqlalchemy import exc
from shared.database.models.crawl_requests import CrawlRequest, CrawlStatus
from sqlmodel.ext.asyncio.session import AsyncSession

from shared.database.engine import engine
from shared.queue.base_publisher import BasePublisher
from .dto.crawl import CrawlRequest as CrawlRequestDTO
from .frontier_grpc_server import serve 
from contextlib import asynccontextmanager
from shared.utils import logger

def start_grpc_server():
  import threading
  grpc_thread = threading.Thread(target=serve, daemon=True)
  grpc_thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
  start_grpc_server()
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
        select_crawl_req_query = select(CrawlRequest).where(CrawlRequest.url == url)
        existing_crawl_request = (await session.exec(select_crawl_req_query)).one()
      except exc.NoResultFound:
        existing_crawl_request = None

    if existing_crawl_request:
      return HTTPException(status_code=409, detail="Crawl request already exists", headers={
        "Location": f"/crawl/status/{existing_crawl_request.id}"
      })
    
    # create crawl request
    crawl_request_mo = CrawlRequest(
      url=url,
      depth=depth,
      max_pages=max_pages,
      status=CrawlStatus.PENDING
    )

    async with AsyncSession(engine) as session:
      try:
        session.add(crawl_request_mo)
        await session.commit()
        # refresh crawl_request_mo to get id later
        await session.refresh(crawl_request_mo)

      except exc.DuplicateColumnError as e:
        logger.error("Duplicate Column: %s", e, exc_info=True)
        return HTTPException(status_code=409, detail="Crawl Request already Exists")
      except Exception as e:
        logger.error("Failed to insert crawl request: %s", e, exc_info=True)
        return HTTPException(status_code=500, detail="Failed to insert crawl request")

    logger.info(f"Created crawl request with ID: {crawl_request_mo.id}")
    
    try:  
      logger.info("Sending crawl request to queue")

      publisher = BasePublisher("crawl_requests")
      crawl_body = crawl_request_mo.model_dump(mode="json")
      
      await publisher.publish("crawl_request", {
        "url": crawl_body["url"],
        "depth": 0
      })

      logger.info(f"Crawl request {crawl_request_mo.id} sent to queue")
      return crawl_request_mo
    except Exception as e:
      logger.error("Failed to publish crawl request: %s", e, exc_info=True)

  except Exception as e:
    logger.error("Internal Server Error: %s", e, exc_info=True)
    return HTTPException(status_code=500, detail="Internal Server Error")
  