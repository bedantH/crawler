from master.infra.queue import get_mq_channel
from shared.config import MAX_TASKS_THRESHOLD
from shared.database.engine import engine
from sqlmodel import Session, select, SQLModel
from shared.database.models.worker import Worker
from shared.database.models.task import Task
from sqlalchemy import func
import uuid

class WorkerStatsModel(SQLModel):
    id: uuid.UUID
    task_count: int

def on_message_callback(ch, method, properties, body):
    with Session(engine) as session:
        existing_tasks_stat_query = (
            select(
                Worker.id,
                func.count(func.distinct(Task.id)).label("task_count"),
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

    # handling a case where there are currently no active workers
    if len(all_workers) == 0:
        # TODO: Start the first worker instance
        pass
    else:
        if all(worker.task_count == MAX_TASKS_THRESHOLD for worker in all_workers):
            # TODO: Create New instance here
            pass
        else:
            least_task_worker = all_workers[0]
            for worker in all_workers:
                if worker.task_count < least_task_worker.task_count:
                    least_task_worker = worker

            # TODO: assign the task to the least loaded instance
        
    print(f" [x] Received {body}") 
    ch.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == "__main__":
    channel = get_mq_channel()
    channel.queue_declare(queue='crawl_requests', durable=True)

    channel.basic_qos(prefetch_count=1)
    print(" [*] Waiting for messages. To exit press CTRL+C")

    channel.basic_consume(queue='crawl_requests', on_message_callback=on_message_callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [x] Stopping consumption")
        channel.stop_consuming()
    finally:
        connection = channel.connection
        connection.close()