import pika

from shared.config import AMQP_URL
from services.slave.src.slave.queue import connection

def get_mq_connection():
    parameters = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(parameters)
    
    return connection

connection = get_mq_connection()

def get_mq_channel():
    channel = connection.channel()
    
    return channel

def close_mq_connection():
    connection.close()