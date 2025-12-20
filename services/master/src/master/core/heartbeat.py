import threading
import time
from master.core.master_grpc_server import serve
from shared.utils import logger
from master.infra.db import DBConnection
from services.master.src.master.config.settings import HEARTBEAT_TIMEOUT

class Heartbeat:
  def __init__(self, timeout: int = 5, check_interval: int = 2) -> None:
    self.check_interval = check_interval
    self.timeout = timeout
    self.running = True

  def init(self):
    timer = threading.Thread(target=self._monitor_loop)
    timer.daemon = True
    timer.start()

    logger.info("Heartbeat looping intialized.")
    logger.info("Looking for dead / unresponsive workers")

    serve()
      
  def _monitor_loop(self):
    while self.running:
      self.mark_dead_workers()
      time.sleep(self.check_interval)

  def mark_dead_workers(self):
    """
    Handling heartbeat response
    """
    db = DBConnection()
    cursor = db.get_cursor()

    get_dead_workers = """
      SELECT id AS worker_id FROM workers
      WHERE (? - last_heartbeat) >= ?;
    """
    
    now = time.time()
    cursor.execute(get_dead_workers, (now, HEARTBEAT_TIMEOUT))

    dead_workers = cursor.fetchall()

    if len(dead_workers) == 0:
      logger.info("No dead workers found at the moment")
    else:
      # TODO: do something with the dead workers:
        # get all the tasks and reschedule them
        # replace the a new worker
      pass

    db.close_conn()