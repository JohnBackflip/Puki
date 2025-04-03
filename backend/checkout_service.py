from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http
from datetime import datetime
import pika
import json

app = Flask(__name__)
CORS(app)

housekeeping_url = "http://localhost:7001/housekeeping"

# RabbitMQ Connection
def get_rabbitmq_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='sms_queue', durable=True)
    return channel, connection

@app.route("/checkout", methods=["POST"])
def checkout():
    room_id = request.json.get("room_id")
    room_json = {"room_id": room_id}
    
    # Invoke Housekeeping service
    housekeeping_result = invoke_http(housekeeping_url, method="POST", json=room_json)
    print("housekeeping result:", housekeeping_result)

    # Retrieve customer's contact
    customer_id = request.json.get("customer_id")
    customer_url = "http://localhost:5003/customers/" + str(customer_id)
    #customer_result = invoke_http(customer_url)
    #customer_contact = customer_result["data"]["contact"]

    # Send feedback form
    data = request.json
    mobile_number = data.get('mobile_number')
    feedback_url = "https://forms.gle/dKzRvA4dDMhsrC8D6"

    if not mobile_number:
        return jsonify({'error': 'Missing mobile number'}), 400

    # Publish to RabbitMQ
    channel, connection = get_rabbitmq_channel()
    message = json.dumps({'mobile_number': mobile_number, 'message': "We would love to hear your feedback: " + feedback_url})
    channel.basic_publish(exchange='', routing_key='sms_queue', body=message)
    connection.close()

    return jsonify({'message': "Check-out successful!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=True)
