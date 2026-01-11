from sqlmodel import Session
from shared.database.engine import engine
from shared.database.models.worker import Worker
from shared.database.models.task import Task, TaskStatus
from sqlalchemy import func
from shared.config import MAX_TASKS_THRESHOLD
from master.core.worker_manager import worker_manager

class WorkerStatsModel(SQLModel):
    id: uuid.UUID
    task_count: int

class TaskDispatcher():
    def __init__():
        worker_manager = WorkerManager()

    def dispatch(self, task_data):
        try:
            """
                Task Dispatcher:
                    task_data = { url: str, depth: int }
            """

            target_worker_id = None

            with Session(engine) as session:
                existing_tasks_stat_query = (
                    select(
                        Worker.id,
                        func.count(func.distinct(Task.id).label("task_count"))
                    )
                    .select_from(Worker)
                    .outerjoin(Task)
                    .group_by(Worker.id, Worker.hostname) # type: ignore
                )

                results = session.exec(existing_tasks_stat_query).all()
                all_workers = [
                    WorkerStatsModel(id=row[0], task_count=row[1])
                    for row in results
                ]
            
            if len(all_workers) == 0 or all(worker.task_count == MAX_TASKS_THRESHOLD for worker in all_workers):
                target_worker_id = self.worker_manager.create_worker() # starts a new worker container and creates respective queues for it
            else:
                least_task_worker = all_workers[0]
                for worker in all_workers:
                    if worker.task_count < least_task_worker.task_count:
                        least_task_worker = worker
                
                target_worker_id = least_task_worker.id

            task = Task(
                payload=json.dumps(task_data),
            )

            with Session(engine) as session:
                session.add(task)
                session.commit()

                task.refresh()

            task_id = task.id
            
            assignment_status = worker_manager.assign_task_to_worker(task_id=task_id, worker_id=target_worker_id)

            if not assignment_status:
                raise Error(f"Failed to assign Task({task_id}) to Worker({target_worker_id})")

            logger.info(f"Successfully assigned Task({task_id}) to Worker({target_worker_id})")

        except Exception as e:
            logger.error("Error occurred when dispatching a task: %s", e)
            raise
