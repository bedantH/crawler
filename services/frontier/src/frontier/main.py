from fastapi import FastAPI, HTTPException, Request

from frontier.models.crawl_request import CrawlRequestDocument, CrawlStatus
import pika
from .mq.queue import get_mq_channel
from .dto.crawl import CrawlRequest
from .frontier_grpc_server import serve
from contextlib import asynccontextmanager
from .db import init_db
from .utils.logger import logger
import json

def start_grpc_server():
  import threading
  grpc_thread = threading.Thread(target=serve, daemon=True)
  grpc_thread.start()

def create_queue_client():
  channel = get_mq_channel()
  channel.queue_declare(queue='crawl_requests', durable=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
  client = await init_db()
  start_grpc_server()
  create_queue_client()
  logger.info("Frontier service started")
  
  try:
    yield
  finally:
    client.close()
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
async def crawl(request: Request, crawl_request: CrawlRequest):
  # Implement the crawl logic here
  # TODO: 
    # Create an object in MongoDB called crawl_request, with a unique ID
    # Queue the crawl request for processing, using the unique ID as the queue item ID
    # Update redis records for the URL and ID
    # Next, update the status of the crawl request in MongoDB to "queued"
    # And return a crawl request ID for polling in future
    # Rest will be handled by the worker master when it reads the crawl request from the queue
  
  url = crawl_request.url
  depth: int = crawl_request.depth
  max_pages = crawl_request.max_pages
  
  # find crawl request by url
  existing_crawl_request = await CrawlRequestDocument.find_one({"url": url})
  
  if existing_crawl_request:
    return HTTPException(status_code=409, detail="Crawl request already exists", headers={
      "Location": f"/crawl/status/{existing_crawl_request.id}"
    })
  
  # create crawl request
  crawl_request_mo = CrawlRequestDocument(
    url=url,
    depth=depth,
    max_pages=max_pages,
    status=CrawlStatus.PENDING
  )
  
  await crawl_request_mo.save()
  
  logger.info(f"Created crawl request with ID: {crawl_request_mo.id}")
  logger.info("Sending crawl request to queue")

  channel = get_mq_channel()
  crawl_body = crawl_request_mo.model_dump(mode="json")
  channel.basic_publish(
    exchange='',
    routing_key='crawl_requests',
    body=json.dumps({
      "url": crawl_body["url"],
      "depth": 0
    }),
    properties=pika.BasicProperties(
      delivery_mode=2,
    )
  )

  logger.info(f"Crawl request {crawl_request_mo.id} sent to queue")

  return crawl_request_mo