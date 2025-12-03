import pika

from shared.config import AMQP_URL

def get_mq_connection():
    parameters = pika.URLParameters(AMQP_URL)
    connection = pika.BlockingConnection(parameters)
    
    return connection

def get_mq_channel():
    connection = get_mq_connection()
    channel = connection.channel()
    
    return channel

def close_mq_connection(connection):
    connection.close()