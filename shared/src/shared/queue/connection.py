import pika
from shared.config import AMQP_URL
import threading
from contextlib import contextmanager

class MQConnection:
    _connection = None
    _lock = threading.Lock()

    def __init__(self):
        self.url = AMQP_URL

    def connect(self):
        """Establish a new connection if not exists."""
        with self._lock:
            if not MQConnection._connection or MQConnection._connection.is_closed:
                params = pika.URLParameters(self.url)
                MQConnection._connection = pika.BlockingConnection(params)
        return MQConnection._connection

    @contextmanager
    def channel(self):
        """Provide a channel and close it automatically."""
        connection = self.connect()
        ch = connection.channel()
        try:
            yield ch
        finally:
            if ch.is_open:
                ch.close()

    def close(self):
        # close the connection and any channels here
        if MQConnection._connection:
            if not MQConnection._connection.is_closed:
                MQConnection._connection.close()
            MQConnection._connection = None