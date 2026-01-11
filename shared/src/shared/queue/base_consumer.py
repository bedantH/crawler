import json
from .connection import MQConnection
from .exchange import Exchange

class BaseConsumer:
    def __init__(self, exchange_name: str, queue_name: str, routing_key: str, exchange_type='direct', prefetch_count: int = 1):
        self.connection = MQConnection()
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.routing_key = routing_key
        self.exchange_type = exchange_type
        self.prefetch_count = prefetch_count

    def on_message(self, ch, method, properties, body):
        """Override this method in subclasses"""
        message = json.loads(body)
        print("Received:", message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start(self):
        with self.connection.channel() as ch:
            exchange = Exchange(ch, self.exchange_name, self.exchange_type)
            exchange.declare()
            
            ch.queue_declare(queue=self.queue_name, durable=True)
            ch.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.routing_key)

            ch.basic_qos(prefetch_count=self.prefetch_count)
            
            ch.basic_consume(queue=self.queue_name, on_message_callback=self.on_message)
            print(f" [*] Waiting for messages on {self.queue_name}. To exit press CTRL+C")
            ch.start_consuming()
