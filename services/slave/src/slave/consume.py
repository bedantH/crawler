import os
from .queue import get_mq_channel, close_mq_connection
from .handler import on_message_callback

def start_consume():
  channel = get_mq_channel()
  channel.queue_declare(queue=os.getenv("WORKER_ID"), durable=True)

  channel.basic_qos(prefetch_count=1)

  channel.basic_consume(queue=os.getenv("WORKER_ID"), on_message_callback=on_message_callback)

  print(" [*] Waiting for messages. To exit press CTRL+C")

  try:
    channel.start_consuming()
  except KeyboardInterrupt:
    channel.stop_consuming()
  finally:
    close_mq_connection()