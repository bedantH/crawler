from enum import Enum
from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy import Index
import uuid

class CrawlStatus(str, Enum):
  PENDING = "pending"
  IN_PROGRESS = "in_progress"
  COMPLETED = "completed"
  FAILED = "failed"

class CrawlRequest(SQLModel, table=True):
  __table_args__ = (
      Index("idx_crawl_status_created", "status", "created_at"),
      Index("idx_crawl_status_updated", "status", "updated_at"),
    )

  id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
  url: str = Field(nullable=False, unique=True, index=True)
  max_depth: int = Field(default=1, ge=1, le=10)
  max_pages: int = Field(default=50, ge=1, le=100)
  status: CrawlStatus = Field(default=CrawlStatus.PENDING, nullable=False, index=True)

  created_at: datetime = Field(default_factory=datetime.utcnow)
  updated_at: datetime = Field(default_factory=datetime.utcnow)