import pika
import json
import requests
from telesign.messaging import MessagingClient

# Telesign API Credentials
TELESIGN_CUSTOMER_ID = "58F7A11F-17B7-420E-B011-2F45F2AE226F"
TELESIGN_API_KEY = "eB4oSInrnVpwiEN6EMoy5IJ5S2Tpthxh8AGN0Pe9M5kOcQ+unVyS8jZY82d7xNXuz1hHnlhUvbEFUAXTf/w6mg=="

def send_sms(mobile_number, message):
    message_type = "ARN"

    messaging = MessagingClient(TELESIGN_CUSTOMER_ID, TELESIGN_API_KEY)
    response = messaging.message(mobile_number, message, message_type)
    print(f"\nResponse:\n{response.body}\n")

# RabbitMQ Consumer
def callback(ch, method, properties, body):
    data = json.loads(body)
    mobile_number = "+65" + data.get('mobile_number')
    message = data.get('message')

    if mobile_number:
        print(f"Received SMS request for {mobile_number}")
        send_sms(mobile_number, message)

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.queue_declare(queue='sms_queue', durable=True)

channel.basic_consume(queue='sms_queue', on_message_callback=callback, auto_ack=True)

print("📡 Waiting for messages. To exit, press CTRL+C")
channel.start_consuming()
