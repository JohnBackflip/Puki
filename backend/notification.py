from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
from os import environ
from telesign.messaging import MessagingClient
import threading

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# Get RabbitMQ URL from environment variable
RABBITMQ_URL = environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

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
        print(f"📩 Received SMS request for {mobile_number}")
        send_sms(mobile_number, message)

def consume_messages():
    try:
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue='sms_queue', durable=True)

        channel.basic_consume(queue='sms_queue', on_message_callback=callback, auto_ack=True)

        print("📡 Waiting for messages. To exit, press CTRL+C")
        channel.start_consuming()
    except Exception as e:
        print(f"Error in RabbitMQ consumer: {str(e)}")
        # Try to reconnect after a delay
        threading.Timer(5.0, consume_messages).start()

# Start RabbitMQ consumer in a separate thread
consumer_thread = threading.Thread(target=consume_messages)
consumer_thread.daemon = True
consumer_thread.start()

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/notify", methods=["POST"])
def send_notification():
    try:
        data = request.get_json()
        message = data.get("message")
        recipient = data.get("recipient")
        notification_type = data.get("type", "SMS")

        if not message or not recipient:
            return jsonify({"error": "Message and recipient are required"}), 400

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        channel = connection.channel()

        # Declare queue
        queue_name = f"{notification_type.lower()}_queue"
        channel.queue_declare(queue=queue_name, durable=True)

        # Prepare message
        notification = {
            "message": message,
            "recipient": recipient,
            "type": notification_type
        }

        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(notification),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )

        connection.close()

        return jsonify({
            "message": "Notification sent successfully",
            "type": notification_type
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to send notification: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)