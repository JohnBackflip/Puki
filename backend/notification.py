from flask import Flask, request, jsonify
from flask_cors import CORS
import pika
import json
from os import environ
from telesign.messaging import MessagingClient
import threading
from amqp_connection import create_connection
import time

app = Flask(__name__)
CORS(app)

# Get RabbitMQ URL from environment variable
RABBITMQ_URL = environ.get('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

# Telesign API Credentials
TELESIGN_CUSTOMER_ID = environ.get('TELESIGN_CUSTOMER_ID', "58F7A11F-17B7-420E-B011-2F45F2AE226F")
TELESIGN_API_KEY = environ.get('TELESIGN_API_KEY', "eB4oSInrnVpwiEN6EMoy5IJ5S2Tpthxh8AGN0Pe9M5kOcQ+unVyS8jZY82d7xNXuz1hHnlhUvbEFUAXTf/w6mg==")

def send_sms(mobile_number, message):
    try:
        # Ensure mobile number starts with +65 and has exactly 8 digits after
        if not mobile_number.startswith('+65'):
            mobile_number = '+65' + mobile_number.lstrip('0')
        
        if len(mobile_number) != 11:  # +65 + 8 digits
            raise ValueError(f"Invalid mobile number format: {mobile_number}")
            
        message_type = "ARN"
        messaging = MessagingClient(TELESIGN_CUSTOMER_ID, TELESIGN_API_KEY)
        print(f"Sending SMS to {mobile_number}: {message}")
        response = messaging.message(mobile_number, message, message_type)
        print(f"Response from Telesign: {response.body}")
        return True
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return False

# RabbitMQ Consumer
def callback(ch, method, properties, body):
    try:
        data = json.loads(body)
        mobile_number = data.get('recipient', '')
        message = data.get('message', '')

        if not mobile_number or not message:
            print("Invalid message data received: missing mobile number or message")
            return

        print(f"📩 Received SMS request for {mobile_number}")
        success = send_sms(mobile_number, message)
        if not success:
            print(f"Failed to send SMS to {mobile_number}")
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        
def consume_messages():
    while True:
        try:
            # Create a new connection
            connection = create_connection()
            channel = connection.channel()
            channel.queue_declare(queue='sms_queue', durable=True)

            print("📡 Waiting for messages. To exit, press CTRL+C")
            channel.basic_consume(queue='sms_queue', on_message_callback=callback, auto_ack=True)
            channel.start_consuming()
        except Exception as e:
            print(f"Error in RabbitMQ consumer: {str(e)}")
            # Try to reconnect after a delay
            time.sleep(5)

# Start RabbitMQ consumer in a separate thread
consumer_thread = threading.Thread(target=consume_messages)
consumer_thread.daemon = True
consumer_thread.start()

# health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# send notification
@app.route("/notify", methods=["POST"])
def send_notification():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400

        message = data.get("message")
        recipient = data.get("recipient")
        notification_type = data.get("type", "SMS")

        if not message or not recipient:
            return jsonify({"error": "Message and recipient are required"}), 400

        print(f"Received notification request: {data}")

        # For direct SMS sending without queue
        # if notification_type == "SMS":
        #     success = send_sms(recipient, message)
        #     if success:
        #         return jsonify({
        #             "message": "SMS sent successfully",
        #             "type": notification_type
        #         }), 200
        #     else:
        #         return jsonify({"error": "Failed to send SMS"}), 500

        # For queued notifications
        try:
            # Create a new connection for publishing
            connection = create_connection()
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
                "message": "Notification queued successfully",
                "type": notification_type
            }), 200

        except Exception as e:
            print(f"Error publishing to queue: {str(e)}")
            return jsonify({"error": f"Failed to queue notification: {str(e)}"}), 500

    except Exception as e:
        print(f"Error in send_notification: {str(e)}")
        return jsonify({"error": f"Failed to send notification: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5007, debug=True)
    
    