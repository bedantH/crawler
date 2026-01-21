import asyncio
from contextlib import asynccontextmanager
from shared.config import AMQP_URL
import aio_pika

class MQConnection:
    _connection = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.url = AMQP_URL

    async def connect(self):
        async with self._lock:
            if not MQConnection._connection or MQConnection._connection.is_closed:
                MQConnection._connection = await aio_pika.connect_robust(self.url)
        return MQConnection._connection

    @asynccontextmanager
    async def channel(self):
        connection = await self.connect()
        ch = await connection.channel()
        
        try:
            yield ch
        finally:
            if ch.closed is False:
                await ch.close()

    async def close(self):
        # close the connection and any channels here
        if MQConnection._connection:
            if not MQConnection._connection.is_closed:
                await MQConnection._connection.close()
            MQConnection._connection = None

    async def get_channel(self):
        connection = await self.connect()
        return await connection.channel()