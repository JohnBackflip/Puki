import time
import pika
from os import environ

hostname = "219.74.5.18"
port = 15672
exchangename = "notification"
exchangetype = "topic"

def create_connection(max_retries=12, retry_interval=5):
    print('amqp_setup:create_connection')
    retries = 0
    connection = None
    while retries < max_retries:
        try:
            print('amqp_setup: Trying connection')
            # connect to the broker and set up a communication channel in the connection
            connection = pika.BlockingConnection(pika.ConnectionParameters
                                (host=hostname, port=port,
                                 heartbeat=3600, blocked_connection_timeout=3600))
            print("amqp_setup: Connection established successfully")
            break  # Connection successful, exit the loop
        except pika.exceptions.AMQPConnectionError as e:
            print(f"amqp_setup: Failed to connect: {e}")
            retries += 1
            print(f"amqp_setup: Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)

    if connection is None:
        raise Exception("amqp_setup: Unable to establish a connection to RabbitMQ after multiple attempts.")

    return connection

def create_channel(connection):
    print('amqp_setup:create_channel')
    channel = connection.channel()
    # Set up the exchange if the exchange doesn't exist
    print('amqp_setup:create exchange')
    channel.exchange_declare(exchange=exchangename, exchange_type=exchangetype, durable=True) # 'durable' makes the exchange survive broker restarts
    return channel

def create_queues(channel):
    print('amqp_setup:create queues')
    create_notification_queue(channel)

def create_notification_queue(channel):
    print('amqp_setup:create_OrderInfo_queue')
    a_queue_name = 'notification'
    channel.queue_declare(queue=a_queue_name, durable=True)
    channel.queue_bind(exchange=exchangename, queue=a_queue_name, routing_key='notification')



if __name__ == "__main__":  # execute this program only if it is run as a script (not by 'import')   
    connection = create_connection()
    channel = create_channel(connection)
    create_queues(channel)
    