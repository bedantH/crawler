from datetime import datetime
from enum import Enum
from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Index
import uuid

class WorkerStatus(Enum):
  IDLE = "idle"
  RUNNING = "running"
  BUSY = "busy"
  FAILED = "failed"
  STOPPED = "stopped"
  SHUTTING_DOWN = "shutting_down"

class Worker(SQLModel, table=True):
  __table_args__ = (
      Index("idx_worker_status", "status"),
      Index("idx_worker_last_heartbeat", "last_heartbeat"),
  )

  id: uuid.UUID = Field(primary_key=True)
  hostname: str = Field(nullable=False)

  status: WorkerStatus = Field(nullable=False, default=WorkerStatus.IDLE)  # idle, busy, failed, shutting_down

  last_heartbeat: Optional[datetime] = None
  created_at: datetime = Field(default_factory=datetime.utcnow)
  registered_at: datetime = Field(nullable=False)

  total_tasks_completed: int = Field(default=0, nullable=False)
  tasks_in_queue: int = Field(default=0, nullable=False)