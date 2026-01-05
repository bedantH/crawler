import json
import pika
from .connection import MQConnection
from .exchange import Exchange

class BasePublisher:
    def __init__(self, exchange_name: str, exchange_type='direct'):
        self.connection = MQConnection()
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type

    def publish(self, routing_key: str, message: dict):
        with self.connection.channel() as ch:
            exchange = Exchange(ch, self.exchange_name, self.exchange_type)
            exchange.declare()
            ch.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    content_type='application/json',
                    delivery_mode=2  # persistent messages
                )
            )
