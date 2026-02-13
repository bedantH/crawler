from datetime import datetime
from sqlmodel import SQLModel, Field, Column
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Index
import uuid
from enum import Enum

class TaskStatus(Enum):
  PENDING = "pending"
  ASSIGNED = "assigned"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"
  RESCHEDULED = "rescheduled"
  CANCELLED = "cancelled"

class Task(SQLModel, table=True):
  __table_args__ = (
        Index("idx_task_status_created", "status", "created_at"),
        Index("idx_task_worker_status", "worker_id", "status"),
    )

  id: uuid.UUID = Field(
    sa_column=Column(UUID(as_uuid=True), primary_key=True),
    default_factory=uuid.uuid4
  )

  worker_id: uuid.UUID = Field(
      default=None,
      foreign_key="worker.id",
  )

  payload: Optional[str] = Field(nullable=True)
  status: TaskStatus = Field(nullable=False, default=TaskStatus.PENDING) # Pending, Assigned, Running, Completed, Failed, Rescheduled, Cancelled
  retries: int = Field(default=0, nullable=False)

  created_at: datetime = Field(default_factory=datetime.utcnow)
  started_at: Optional[datetime] = None
  finished_at: Optional[datetime] = None

  error: Optional[str] = None
