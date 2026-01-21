import json
import aio_pika
from .connection import MQConnection
from .exchange import Exchange

class BasePublisher:
    def __init__(self, exchange_name: str, exchange_type='direct'):
        self.connection = MQConnection()
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type

    async def publish(self, routing_key: str, message: dict):
        async with self.connection.channel() as ch:
            exchange = Exchange(ch, self.exchange_name, self.exchange_type)
            abs_exchange = await exchange.declare()
            
            await abs_exchange.publish( 
                aio_pika.Message(
                    body=json.dumps(message).encode('utf-8'),
                    content_type='application/json',
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=routing_key
            )
