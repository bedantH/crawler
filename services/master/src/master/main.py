from .queue import get_mq_channel
from .db import init, cursor
from shared.config import MAX_TASKS_THRESHOLD

def on_message_callback(ch, method, properties, body):
    existing_tasks_stats = """
        SELECT w.id, w.hostname, COUNT(DISTINCT t.id) AS task_count
        FROM workers w
        LEFT JOIN tasks t 
            ON w.id = t.worker_id
        GROUP BY w.id, w.hostname;
    """
    cursor.execute(existing_tasks_stats)
    all_workers = cursor.fetchall()

    # handling a case where there are currently no active workers
    if len(all_workers) == 0:
        # TODO: Start the first worker instance
        pass
    else:
        if all(worker['task_count'] == MAX_TASKS_THRESHOLD for worker in all_workers):
            # TODO: Create New instance here
            pass
        else:
            least_task_worker = all_workers[0]
            for worker in all_workers:
                if worker['task_count'] < least_task_worker:
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
        init()
    except KeyboardInterrupt:
        print(" [x] Stopping consumption")
        channel.stop_consuming()
    finally:
        connection = channel.connection
        connection.close()