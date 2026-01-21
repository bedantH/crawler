import asyncio
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

    async def on_message(self, message):
        async with message.process():
            body = message.body
            payload = json.loads(body)
            print("Received:", payload)

    async def start(self, stop_event: asyncio.Event):
        async with self.connection.channel() as ch:
            await ch.set_qos(prefetch_count=self.prefetch_count)

            exchange = Exchange(ch, self.exchange_name, self.exchange_type)
            abs_exchange = await exchange.declare()

            queue = await ch.declare_queue(self.queue_name, durable=True)
            await queue.bind(exchange=abs_exchange, routing_key=self.routing_key)

            print(f" [*] Waiting for messages on {self.queue_name}. To exit press CTRL+C")

            consumer_tag = await queue.consume(self.on_message)

            try:
                await stop_event.wait()
            finally:
                await queue.cancel(consumer_tag)            