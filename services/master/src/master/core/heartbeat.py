import threading
from datetime import datetime, timedelta
import time
from master.core.master_grpc_server import serve
from shared.utils import logger
from shared.database.engine import engine
from sqlmodel import Session, select
from shared.config import HEARTBEAT_TIMEOUT
from shared.database.models.worker import Worker

class Heartbeat:
  def __init__(self, timeout: int = HEARTBEAT_TIMEOUT, check_interval: int = 2) -> None:
    self.check_interval = check_interval
    self.timeout = timeout
    self.running = True

  def init(self):
    timer = threading.Thread(target=self._monitor_loop)
    timer.daemon = True
    timer.start()

    logger.info("Heartbeat looping initialized.")
    logger.info("Looking for dead / unresponsive workers")
      
  def _monitor_loop(self):
    while self.running:
      self.mark_dead_workers()
      time.sleep(self.check_interval)

  def mark_dead_workers(self):
    """
    Handling heartbeat response
    """
    with Session(engine) as session:
      cutoff = datetime.utcnow() - timedelta(seconds=self.timeout)

      dead_workers_st = select(Worker.id).where(
        (Worker.last_heartbeat < cutoff)
      )

      dead_workers = session.exec(dead_workers_st).all()

    if len(dead_workers) > 0:
        logger.info("Dead workers detected: %s", len(dead_workers))
        for worker in dead_workers:
            logger.info("Dead Worker: %s", worker)
