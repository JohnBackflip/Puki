# composite microservice
# Calls Housekeeping service to clean the room
# Publishes SMS feedback link to RabbitMQ (sms_queue)
# Returns a confirmation response

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

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    booking_id = data["booking_id"]
    name = data["name"]

    # verify booking exists
    booking_url = f"{BOOKING_URL}/bookings/{booking_id}"
    booking_response = invokes.invoke_http(booking_url, method="GET")

    if booking_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.get("data")
    guest_id = booking_data["guest_id"]
    check_out = booking_data["check_out"]

    # checks if today is the check-out date
    today = datetime.utcnow().date()
    if today != check_out:
        return jsonify({"code": 400, "message": "Check-out is only allowed on the check-out date."}), 400

    # verify guest exists
    guest_url = f"{GUEST_URL}/guests/{guest_id}"
    guest_response = invokes.invoke_http(guest_url, method="GET")

    if guest_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Guest record not found."}), 400

    guest_data = guest_response.get("data")

    if guest_data["name"].lower() != name.lower():
        return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

    return jsonify({
        "code": 200,
        "message": "Check-out successful. Thank you for staying with us!"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)