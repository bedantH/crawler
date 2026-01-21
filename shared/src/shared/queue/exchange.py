import aio_pika

class Exchange:
    def __init__(self, channel: aio_pika.abc.AbstractChannel, name: str, type_: str = 'direct', durable=True):
        self.channel = channel
        self.name = name
        self.type = type_
        self.durable = durable

    async def declare(self):
        exchange = await self.channel.declare_exchange(
            self.name,
            self.type,
            durable=self.durable
        )

        return exchange
