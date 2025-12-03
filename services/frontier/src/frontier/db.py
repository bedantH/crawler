from motor.motor_asyncio import AsyncIOMotorClient
from .constants.config import MONGO_URI, DATABASE_NAME
from beanie import init_beanie
from .models.crawl_request import CrawlRequestDocument
from .utils.logger import logger

async def init_db():
  try:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    await init_beanie(database=db, document_models=[CrawlRequestDocument]) # type: ignore
    logger.info("Database initialized")
    
    return client
  except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise e