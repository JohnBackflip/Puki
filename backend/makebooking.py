from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import invokes
from os import environ

app = Flask(__name__)
CORS(app)

# Service URLs
BOOKING_URL = environ.get('BOOKING_URL', 'http://localhost:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://localhost:5011')
PRICE_URL = environ.get('PRICE_URL', 'http://localhost:5003')
NOTIFICATION_URL = environ.get('NOTIFICATION_URL', 'http://localhost:5007')

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Make a booking (without room assignment)
@app.route("/makebooking", methods=["POST"])
def create_booking():
    data = request.get_json()
    print("Received data:", data)

    if not data:
        return jsonify({"code": 400, "message": "No data received"}), 400

    # Validate fields
    required_fields = ["guest_id", "room_type", "check_in", "check_out", "price"]
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400

    # Validate dates
    try:
        check_in = datetime.strptime(data["check_in"], "%Y-%m-%d").date()
        check_out = datetime.strptime(data["check_out"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"code": 400, "message": "Invalid date format. Use YYYY-MM-DD."}), 400

    if check_out <= check_in:
        return jsonify({"code": 400, "message": "Check-out date must be later than check-in date."}), 400

    # Verify guest exists
    guest_check_url = f"{GUEST_URL}/guest/{data['guest_id']}"
    guest_response = invokes.invoke_http(guest_check_url, method="GET")
    print("Guest response:", guest_response)

    if not isinstance(guest_response, dict) or guest_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid guest_id. Guest does not exist."}), 400


    # Assemble payload for booking
    booking_payload = {
        "guest_id": data["guest_id"],
        "room_type": data["room_type"],
        "check_in": data["check_in"],
        "check_out": data["check_out"],
        "price": data["price"]
    }

    print("Booking payload to be sent:", booking_payload)

    # Send to booking service
    booking_url = f"{BOOKING_URL}/booking"
    booking_response = invokes.invoke_http(booking_url, method="POST", json=booking_payload)
    print("Booking response:", booking_response)

    if not isinstance(booking_response, dict):
        return jsonify({"code": 500, "message": "Invalid booking response format."}), 500

    if booking_response.get("code") != 201:
        return jsonify({"code": 500, "message": f"Booking creation failed: {booking_response.get('message')}"}), 500

    booking_data = booking_response.get("data")

    
    #hardcoded since the telesign free account only allows for sms to one number 
    guest_phone = "91455020"
    # Send SMS Notification if phone is available
    if guest_phone:
        notification_payload = {
            "recipient": guest_phone,
            "message": (
                f"Your booking is confirmed!\n"
                f"Booking ID: {booking_data['booking_id']}\n"
                f"Room Type: {booking_data['room_type']}\n"
                f"Check-in: {booking_data['check_in']}\n"
                f"Check-out: {booking_data['check_out']}\n"
                f"Thank you for choosing Puki Hotel!"
            ),
            "type": "SMS"
        }
        try:
            notify_response = invokes.invoke_http(f"{NOTIFICATION_URL}/notify", method="POST", json=notification_payload)
            print("Notification sent:", notify_response)
        except Exception as e:
            print(" Failed to send notification:", e)

    return jsonify({"code": 201, "data": booking_response["data"]}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5013, debug=True)
