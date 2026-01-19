from shared.database.models.worker import WorkerStatus
from slave.runtime.consumer import WorkerConsumer

# Represents a worker entity in the slave service
# One instance per worker process, in future workers mapped to threads it will be easier to manage

class Worker:
    def __init__(self, worker_id: str):
        self.worker_id: str = worker_id
        self.status: WorkerStatus = WorkerStatus.IDLE
        self.total_tasks_completed: int = 0
        self.task_in_progress: dict | None = None
        self.consumer: WorkerConsumer | None = None

    def update_status(self, status: WorkerStatus):
        self.status = status

    def invoke_shutdown(self):
        """
            Logic to gracefully shutdown the worker, ensuring current tasks are completed or rescheduled.
        """
        pass

    def cleanup(self):
        self.task_in_progress = None