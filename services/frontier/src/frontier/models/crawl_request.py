from beanie import Document
from pydantic import Field
from datetime import datetime
from enum import Enum

class CrawlStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class CrawlRequestDocument(Document):
  url: str = Field(..., min_length=1, max_length=100)
  depth: int = Field(..., ge=0, le=10)
  max_pages: int = Field(10, ge=1, le=100)
  status: CrawlStatus = Field(CrawlStatus.PENDING)
  
  created_at: datetime = Field(default_factory=datetime.utcnow)
  updated_at: datetime = Field(default_factory=datetime.utcnow)
  
  class Settings:
      name = "crawl_requests"
      indexes = [
          [("url", 1), ("status", 1)]
      ]