# complex microservice 
# Reads booking and guest info from other microservices
# Generates keycard via another microservice

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import invokes
from os import environ

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# Get URLs from environment variables
BOOKING_URL = environ.get('BOOKING_URL', 'http://localhost:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://localhost:5003')
SECURITY_URL = environ.get('SECURITY_URL', 'http://localhost:5010')

@app.route("/health")
def health():
    return {"status": "healthy"}

# self check-in with full_name
@app.route("/self-checkin", methods=["POST"])
def self_checkin():
    data = request.get_json()
    booking_id = data["booking_id"]
    name = data["name"]

    # Check if booking ID and name are provided
    if not booking_id or not name:
        return jsonify({
            "code": 400,
            "message": "Booking ID and full name are required."
        }), 400

    # Verify booking exists
    booking_url = f"{BOOKING_URL}/bookings/{booking_id}"
    booking_response = invokes.invoke_http(booking_url, method="GET")

    if "code" not in booking_response:
        return jsonify({
            "code": 400,
            "message": "Booking service response does not contain 'code' field.",
            "debug": booking_response
        }), 400

    if booking_response.get("code") != 200:
        return jsonify({
            "code": 400,
            "message": "Invalid booking ID.",
            "debug": booking_response  # Include the full response in the debug field
        }), 400

    booking_data = booking_response.get("data")
    guest_id = booking_data["guest_id"]
    room_id = booking_data["room_id"]
    check_in = datetime.strptime(booking_data["check_in"], "%Y-%m-%d").date()

    # Check if today is the check-in date
    today = datetime.utcnow().date()
    if today != check_in:
        return jsonify({
            "code": 400,
            "message": "Check-in is only allowed on the check-in date.",
            "debug": {"today": today, "check_in": check_in}
        }), 400

    # Verify guest exists
    guest_url = f"{GUEST_URL}/guests/{guest_id}"
    guest_response = invokes.invoke_http(guest_url, method="GET")

    if "code" not in guest_response:
        return jsonify({
            "code": 400,
            "message": "Guest service response does not contain 'code' field.",
            "debug": guest_response
        }), 400

    if guest_response.get("code") != 200:
        return jsonify({
            "code": 400,
            "message": "Guest record not found.",
            "debug": guest_response  # Include the guest service response for debugging
        }), 400

    guest_data = guest_response.get("data")

    if guest_data["name"].lower() != name.lower():
        return jsonify({
            "code": 400,
            "message": "Full name does not match booking record.",
            "debug": guest_data
        }), 400

    # Generate keycard in security service
    keycard_url = f"{SECURITY_URL}/keycards"
    keycard_payload = {
        "booking_id": booking_id,
        "guest_id": guest_id,
        "room_id": room_id
    }

    keycard_response = invokes.invoke_http(keycard_url, method="POST", json=keycard_payload)

    if "code" not in keycard_response:
        return jsonify({
            "code": 500,
            "message": "Security service response does not contain 'code' field.",
            "debug": keycard_response
        }), 500

    if keycard_response.get("code") != 200:
        return jsonify({
            "code": 500,
            "message": "Failed to generate keycard.",
            "debug": keycard_response  # Include keycard service response for debugging
        }), 500

    return jsonify({
        "code": 200,
        "message": "Self check-in successful. Use this PIN to access your room.",
        "keycard": keycard_response["data"]
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
