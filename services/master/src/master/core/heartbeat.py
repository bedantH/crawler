from datetime import datetime, timedelta
import time
from master.core.master_grpc_server import serve
from shared.utils import logger
from shared.database.engine import engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from shared.config import HEARTBEAT_TIMEOUT
from shared.database.models.worker import Worker
import asyncio

class Heartbeat:
  def __init__(self, stop_event: asyncio.Event, timeout: int = HEARTBEAT_TIMEOUT, check_interval: int = 2) -> None:
    self.check_interval = check_interval
    self.timeout = timeout
    self._stop_event = stop_event
      
  async def monitor_loop(self):
    logger.info("Heartbeat looping initialized.")
    logger.info("Looking for dead / unresponsive workers")
  
    while not self._stop_event.is_set():
      await self.mark_dead_workers()
      await asyncio.sleep(self.check_interval)

    logger.info("Heartbeat monitoring loop stopped.")

  async def mark_dead_workers(self):
    cutoff = datetime.utcnow() - timedelta(seconds=self.timeout)
    
    async with AsyncSession(engine) as session:
      dead_workers_st = select(Worker.id).where(
        (Worker.last_heartbeat < cutoff)
      )

      dead_workers = (await session.exec(dead_workers_st)).all()

    if len(dead_workers) > 0:
        logger.info("Dead workers detected: %s", len(dead_workers))
        for worker in dead_workers:
            logger.info("Dead Worker: %s", worker)
