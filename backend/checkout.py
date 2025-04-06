from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from os import environ
import json
import pika
import invokes 

app = Flask(__name__)
CORS(app)

# Get URLs from environment variables
BOOKING_URL = environ.get('BOOKING_URL', 'http://booking:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://guest:5011')
HOUSEKEEPING_URL = environ.get('HOUSEKEEPING_URL', 'http://housekeeping:5006')
NOTIFICATION_URL = environ.get('NOTIFICATION_URL', 'http://notification:5007/notify')

# RabbitMQ Connection
def get_rabbitmq_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters('puki-rabbit'))
    channel = connection.channel()
    channel.queue_declare(queue='sms_queue', durable=True)
    return channel, connection

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        data = request.get_json()
        print("Received checkout request:", data)
        
        booking_id = data.get("booking_id")
        name = data.get("name")
        room_id = data.get("room_id")
        mobile_number = data.get("mobile_number")

        if not all([booking_id, name, room_id, mobile_number]):
            return jsonify({"code": 400, "message": "Missing required fields."}), 400

        # 1. Verify booking exists
        booking_url = f"{BOOKING_URL}/booking/{booking_id}"
        print("Fetching booking from:", booking_url)
        booking_response = invokes.invoke_http(booking_url, method="GET")
        print("Booking response:", booking_response)

        if booking_response.get("code") != 200:
            return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

        booking_data = booking_response.get("data")
        guest_id = booking_data["guest_id"]
        check_out_str = booking_data["check_out"]
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        today = datetime.today().date()

        if today != check_out:
            return jsonify({
                "code": 400,
                "message": f"Check-out is only allowed on the check-out date ({check_out_str}). Today is {today}."
            }), 400

        # 2. Verify guest exists
        guest_url = f"{GUEST_URL}/guest/{guest_id}"
        print("Fetching guest from:", guest_url)
        guest_response = invokes.invoke_http(guest_url, method="GET")
        print("Guest response:", guest_response)

        if guest_response.get("code") != 200:
            return jsonify({"code": 400, "message": "Guest record not found."}), 400

        guest_data = guest_response.get("data")
        if guest_data["name"].lower() != name.lower():
            return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

        # 3. Trigger housekeeping
        room_json = {"room_id": room_id}
        print("Triggering housekeeping for room:", room_id)
        housekeeping_result = invokes.invoke_http(HOUSEKEEPING_URL, method="POST", json=room_json)
        print("Housekeeping result:", housekeeping_result)

        # 4. Send SMS with feedback form
        feedback_url = "https://forms.gle/dKzRvA4dDMhsrC8D6"
        # sms_message = f"Thank you for staying with us, {name}! Please provide your feedback: {feedback_url}"
        # channel, connection = get_rabbitmq_channel()
        # message = json.dumps({'mobile_number': mobile_number, 'message': "Thank you for staying with Puki! We would love to hear your feedback: " + feedback_url})
        # channel.basic_publish(exchange='', routing_key='sms_queue', body=message)
        # connection.close()
        try:
            # msg = {
            # "message": sms_message,
            # "recipient": mobile_number,
            # "type": "SMS"
            # }
            # notification_result = invokes.invoke_http(NOTIFICATION_URL, method="POST", json=msg)
            # return notification_result
            # Publish to RabbitMQ (Doesn't work anymore)
            channel, connection = get_rabbitmq_channel()
            message = json.dumps({'mobile_number': mobile_number, 'message': "Thank you for staying with Puki! We would love to hear your feedback: " + feedback_url})
            channel.basic_publish(exchange='', routing_key='sms_queue', body=message)
            connection.close()
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            # Continue with checkout even if SMS fails

        return jsonify({
            "code": 200,
            "message": "Check-out successful. Thank you for staying with us!"
        }), 200

    except Exception as e:
        print(f"Error in checkout: {str(e)}")
        return jsonify({"code": 500, "message": "An error occurred during checkout."}), 500

# For testing
@app.route("/sms", methods=["POST"])
def sms():
    data = request.get_json()
    mobile_number = data.get("mobile_number")
    feedback_url = "https://forms.gle/dKzRvA4dDMhsrC8D6"
    channel, connection = get_rabbitmq_channel()
    message = json.dumps({'mobile_number': mobile_number, 'message': "Thank you for staying with Puki! We would love to hear your feedback: " + feedback_url})
    channel.basic_publish(exchange='', routing_key='sms_queue', body=message)
    connection.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
