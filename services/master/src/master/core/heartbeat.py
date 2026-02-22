from datetime import datetime, timedelta
from shared.utils import logger
from shared.database.engine import engine
from sqlmodel import select, update
from sqlmodel.ext.asyncio.session import AsyncSession
from shared.config import HEARTBEAT_TIMEOUT
from shared.database.models.worker import Worker, WorkerStatus
from shared.database.models.task import Task, TaskStatus
import asyncio


class Heartbeat:
  def __init__(self, stop_event: asyncio.Event, timeout: int = HEARTBEAT_TIMEOUT, check_interval: int = 2) -> None:
    self.check_interval = check_interval
    self.timeout = timeout
    self._stop_event = stop_event

  async def monitor_loop(self):
    logger.info("Heartbeat looping initialized.")
    logger.info("Looking for dead / unresponsive workers every %ss", self.check_interval)

    while not self._stop_event.is_set():
      await self.mark_dead_workers()
      await asyncio.sleep(self.check_interval)

    logger.info("Heartbeat monitoring loop stopped.")

  async def mark_dead_workers(self):
    # Lazy imports to avoid circular dependency at module load time
    from master.core.worker_manager import WorkerManager
    from master.core.task_dispatcher import TaskDispatcher

    cutoff = datetime.utcnow() - timedelta(seconds=self.timeout)

    async with AsyncSession(engine) as session:
      dead_workers_st = select(Worker).where(
        (Worker.last_heartbeat < cutoff)
        & (Worker.status != WorkerStatus.STOPPED)
        & (Worker.status != WorkerStatus.FAILED)
      )
      dead_workers = (await session.exec(dead_workers_st)).all()

    if not dead_workers:
      return

    logger.warning("[heartbeat] %s dead worker(s) detected", len(dead_workers))
    worker_manager = WorkerManager()
    dispatcher = TaskDispatcher()

    for worker in dead_workers:
      worker_id = str(worker.id)
      logger.warning(
        "[heartbeat] Worker %s (hostname=%s) last seen at %s — killing",
        worker_id, worker.hostname, worker.last_heartbeat,
      )

      # find all tasks still assigned/running on this worker
      async with AsyncSession(engine) as session:
        stuck_tasks_st = select(Task).where(
          (Task.worker_id == worker.id)
          & (Task.status.in_([TaskStatus.ASSIGNED, TaskStatus.RUNNING]))  # type: ignore
        )
        stuck_tasks = (await session.exec(stuck_tasks_st)).all()

      logger.info(
        "[heartbeat] Worker %s has %s task(s) to reschedule",
        worker_id, len(stuck_tasks),
      )

      # kill the container and mark worker STOPPED in DB
      killed = await worker_manager.kill_worker(worker_id=worker_id)
      if killed:
        logger.info("[heartbeat] ✓ Worker %s stopped and marked STOPPED in DB", worker_id)
      else:
        logger.error("[heartbeat] ✗ Failed to kill worker %s", worker_id)

      # reschedule stuck tasks — mark as RESCHEDULED then dispatch to another worker
      for task in stuck_tasks:
        task_id = str(task.id)
        try:
          # mark the tasks as RESCHEDULED
          async with AsyncSession(engine) as session:
            await session.exec(
              update(Task)
              .where(Task.id == task.id)  # type: ignore
              .values(status=TaskStatus.RESCHEDULED)
            )
            await session.commit()

          logger.info(
            "[heartbeat] → Rescheduling task %s (was on dead worker %s)",
            task_id, worker_id,
          )
          await dispatcher.dispatch_by_task_id(
            task_id=task_id,
            exclude_worker_id=worker_id,
          )
          logger.info("[heartbeat] ✓ Task %s rescheduled successfully", task_id)

        except Exception as e:
          logger.error(
            "[heartbeat] ✗ Failed to reschedule task %s: %s",
            task_id, e,
            exc_info=True,
          )
