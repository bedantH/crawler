import datetime
from shared.database.models.worker import Worker, WorkerStatus
from master.infra.create_worker import create_worker_container
import uuid
from sqlmodel import Session, engine
from shared.utils import logger

class WorkerManager:
    def __init__(self):
        pass

    def create_worker(self):
        try:
            worker_id = str(uuid.uuid4())
            hostname = f"worker-{worker_id[:5]}"

            worker = Worker(
                id=worker_id,
                hostname=hostname,
                status=WorkerStatus.IDLE,
                registered_at=datetime.utcnow()
            )

            status = create_worker_container(hostname)

            if status is True:
                with Session(engine) as session:
                    session.add(worker)
                    session.commit()
                
                return worker_id
            else:
                logger.error("Failed to create worker container for worker ID: %s", worker_id)
                return None
        except Exception as e:
            logger.error("Error creating worker: %s", e, exc_info=True)
            return None
        
    def assign_task_to_worker(self, task_id: int, worker_id: int):
        pass

    def kill_worker(self, worker_id: int):
        pass

    def get_worker_status(self, worker_id: int):
        pass