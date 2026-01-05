class Exchange:
    def __init__(self, channel, name: str, type_: str = 'direct', durable=True):
        self.channel = channel
        self.name = name
        self.type = type_
        self.durable = durable

    def declare(self):
        self.channel.exchange_declare(
            exchange=self.name,
            exchange_type=self.type,
            durable=self.durable
        )
