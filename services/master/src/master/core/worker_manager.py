import json
from datetime import datetime
from shared.database.models.worker import Worker, WorkerStatus
from shared.database.models.task import Task, TaskStatus
from master.infra.create_worker import create_worker_container
import docker
from docker import errors as docker_errors
import uuid
from sqlmodel import Session
from shared.database.engine import engine
from shared.utils import logger
from shared.queue.base_publisher import BasePublisher

class WorkerManager:
    def __init__(self):
        pass

    def create_worker(self):
        try:
            worker_uuid = uuid.uuid4()
            worker_id = str(worker_uuid)
            hostname = f"worker-{worker_id[:5]}"

            worker = Worker(
                id=worker_uuid,
                hostname=hostname,
                status=WorkerStatus.IDLE,
                registered_at=datetime.utcnow()
            )

            status = create_worker_container(worker_id)

            if status is True:
                with Session(engine) as session:
                    session.add(worker)
                    session.commit()

                    worker.refresh()
                
                return worker_id
            else:
                logger.error("Failed to create worker container for worker ID: %s", worker_id)
                return None
        except Exception as e:
            logger.error("Error creating worker: %s", e, exc_info=True)
            return None
        
    def assign_task_to_worker(self, task_id, worker_id):
        try:
            task_uuid = uuid.UUID(str(task_id))
            worker_uuid = uuid.UUID(str(worker_id))
            with Session(engine) as session:
                task = session.get(Task, task_uuid)
                worker = session.get(Worker, worker_uuid)
                if not task:
                    logger.error("Task not found: %s", task_id)
                    return False
                if not worker:
                    logger.error("Worker not found: %s", worker_id)
                    return False

                task.worker_id = worker.id
                task.status = TaskStatus.ASSIGNED
                worker.tasks_in_queue = (worker.tasks_in_queue or 0) + 1

                session.add(task)
                session.add(worker)
                session.commit()
            
            payload = json.loads(task.payload)
            
            publisher = BasePublisher(f"worker_{worker_id}")
            publisher.publish(f"worker_{worker_id}_task", payload)

            logger.info(f"Task({task_id}) pushed to worker's queue")

            return True
        except Exception as e:
            logger.error("Error assigning task to worker: %s", e, exc_info=True)
            return False

    def kill_worker(self, worker_id):
        try:
            worker_uuid = uuid.UUID(str(worker_id))
            with Session(engine) as session:
                worker = session.get(Worker, worker_uuid)
                if not worker:
                    logger.error("Worker not found: %s", worker_id)
                    return False

                try:
                    client = docker.from_env()
                    container = client.containers.get(str(worker_id))
                    container.stop(timeout=5)
                    container.remove()
                except docker_errors.NotFound:
                    logger.warning("Container for worker %s not found", worker_id)
                except Exception as e:
                    logger.error("Error stopping/removing container for worker %s: %s", worker_id, e, exc_info=True)

                worker.status = WorkerStatus.STOPPED
                session.add(worker)
                session.commit()

            return True
        except Exception as e:
            logger.error("Error killing worker: %s", e, exc_info=True)
            return False

    def get_worker_status(self, worker_id):
        try:
            worker_uuid = uuid.UUID(str(worker_id))
            with Session(engine) as session:
                worker = session.get(Worker, worker_uuid)
                if not worker:
                    logger.error("Worker not found: %s", worker_id)
                    return None
                return worker.status
        except Exception as e:
            logger.error("Error getting worker status: %s", e, exc_info=True)
            return None
