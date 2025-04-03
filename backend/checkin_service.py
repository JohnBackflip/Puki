import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

app.json.sort_keys = False 

# self check-in with full_name
@app.route("/self-checkin", methods=["POST"])
def self_checkin():
    data = request.get_json()
    booking_id = data["booking_id"]
    full_name = data["full_name"] 

    # verify booking exists
    booking_url = f"http://localhost:5002/bookings/{booking_id}"
    booking_response = requests.get(booking_url)

    if booking_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.json()["data"]
    customer_id = booking_data["customer_id"]
    room_id = booking_data["room_id"]
    check_in_date = datetime.strptime(booking_data["check_in_date"], "%Y-%m-%d").date()

    # checks if today is the check-in date
    today = datetime.utcnow().date()
    if today != check_in_date:
        return jsonify({"code": 400, "message": "Check-in is only allowed on the check-in date."}), 400

    # verify customer exists and is Verified
    customer_url = f"http://localhost:5003/customers/{customer_id}"
    customer_response = requests.get(customer_url)

    if customer_response.status_code != 200:
        return jsonify({"code": 400, "message": "Customer record not found."}), 400

    customer_data = customer_response.json()["data"]

    if not customer_data["verified"]:
        return jsonify({"code": 400, "message": "Customer is not verified."}), 400

    if customer_data["name"].lower() != full_name.lower():  
        return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

    # generate keycard in `security_service`
    keycard_url = "http://localhost:5004/keycards"
    keycard_payload = {
        "booking_id": booking_id,
        "customer_id": customer_id,
        "room_id": room_id
    }

    keycard_response = requests.post(keycard_url, json=keycard_payload)

    if keycard_response.status_code != 201:
        return jsonify({"code": 500, "message": "Failed to generate keycard."}), 500

    keycard_data = keycard_response.json()["data"]

    # update booking status to `CHECKED-IN`
    update_booking_url = f"http://localhost:5002/bookings/{booking_id}"
    update_payload = {"status": "CHECKED-IN"}
    requests.put(update_booking_url, json=update_payload)

    return jsonify({
        "code": 200,
        "message": "Self check-in successful. Use this PIN to access your room.",
        "keycard": keycard_data
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
