import json
import uuid
from sqlmodel import SQLModel, select
from shared.database.engine import engine
from shared.database.models.worker import Worker
from shared.database.models.task import Task, TaskStatus
from sqlalchemy import func
from shared.config import MAX_TASKS_THRESHOLD
from master.core.worker_manager import WorkerManager
from shared.utils import logger
from sqlmodel.ext.asyncio.session import AsyncSession


class WorkerStatsModel(SQLModel):
    id: uuid.UUID
    task_count: int


class TaskDispatcher:
    def __init__(self):
        self.worker_manager = WorkerManager()

    async def get_available_worker(self, exclude_worker_id: str | None = None) -> str:
        target_worker_id = None
        try:
            async with AsyncSession(engine) as session:
                if exclude_worker_id:
                    query = (
                        select(Worker.id, func.count(Task.id).label("task_count")) # type: ignore
                        .select_from(Worker)
                        .outerjoin(Task, Task.worker_id == Worker.id) # type: ignore
                        .where(Worker.id != exclude_worker_id)
                        .group_by(Worker.id) # type: ignore
                    )
                else:
                    query = (
                        select(Worker.id, func.count(Task.id).label("task_count")) # type: ignore
                        .select_from(Worker)
                        .outerjoin(Task, Task.worker_id == Worker.id) # type: ignore
                        .group_by(Worker.id) #type: ignore
                    )

                results = (await session.exec(query)).all()
                all_workers = [
                    WorkerStatsModel(id=row[0], task_count=row[1]) for row in results
                ]

                logger.info(f"All workers: {all_workers}")

                if len(all_workers) == 0 or all(
                    worker.task_count == MAX_TASKS_THRESHOLD for worker in all_workers
                ):
                    logger.info("Creating a new worker")
                    target_worker_id = await self.worker_manager.create_worker()  # starts a new worker container and creates respective queues for it
                else:
                    logger.info("Assigning to the least busy worker")
                    least_task_worker = all_workers[0]
                    for worker in all_workers:
                        if worker.task_count < least_task_worker.task_count:
                            least_task_worker = worker

                    target_worker_id = least_task_worker.id

            return str(target_worker_id)
        except Exception as e:
            logger.error("Error getting the available worker: %s", e)
            raise

    async def dispatch_by_task_id(self, task_id, exclude_worker_id: str | None = None):
        try:
            target_worker_id = await self.get_available_worker(
                exclude_worker_id=exclude_worker_id
            )

            if not target_worker_id:
                raise Exception("No available worker found")

            assignment_status = await self.worker_manager.assign_task_to_worker(
                task_id=task_id, worker_id=target_worker_id
            )
            
            if not assignment_status:
                raise Exception(
                    f"Failed to assign Task({task_id}) to Worker({target_worker_id})"
                )

            logger.info(
                f"Successfully assigned Task({task_id}) to Worker({target_worker_id})"
            )

        except Exception as e:
            logger.error("Error occurred when dispatching a task: %s", e)
            raise

    async def dispatch(self, task_data):
        try:
            target_worker_id = await self.get_available_worker()
                
            task = Task(
                payload=json.dumps(task_data),
                crawl_id=task_data['crawl_id']
            )

            async with AsyncSession(engine) as session:
                session.add(task)
                await session.commit()
                await session.refresh(task)

            task_id = task.id

            assignment_status = await self.worker_manager.assign_task_to_worker(
                task_id=task_id, worker_id=target_worker_id
            )

            if not assignment_status:
                raise Exception(
                    f"Failed to assign Task({task_id}) to Worker({target_worker_id})"
                )

            logger.info(
                f"Successfully assigned Task({task_id}) to Worker({target_worker_id})"
            )

        except Exception as e:
            logger.error("Error occurred when dispatching a task: %s", e)
            raise
