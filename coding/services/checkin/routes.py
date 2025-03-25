from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

checkin_bp = Blueprint("checkin_bp", __name__)

@checkin_bp.route("/self-checkin", methods=["POST"])
def self_checkin():
    data = request.get_json()
    booking_id = data["booking_id"]
    full_name = data["full_name"]

    # Verify booking exists
    booking_url = f"http://localhost:5002/bookings/{booking_id}"
    booking_response = requests.get(booking_url)

    if booking_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.json()["data"]
    customer_id = booking_data["customer_id"]
    room_id = booking_data["room_id"]
    check_in_date = datetime.strptime(booking_data["check_in_date"], "%Y-%m-%d").date()

    # Must check in on check-in date
    today = datetime.utcnow().date()
    if today != check_in_date:
        return jsonify({"code": 400, "message": "Check-in is only allowed on the check-in date."}), 400

    # Verify customer exists and is verified
    customer_url = f"http://localhost:5003/customers/{customer_id}"
    customer_response = requests.get(customer_url)

    if customer_response.status_code != 200:
        return jsonify({"code": 400, "message": "Customer record not found."}), 400

    customer_data = customer_response.json()["data"]
    if not customer_data["verified"]:
        return jsonify({"code": 400, "message": "Customer is not verified."}), 400

    if customer_data["name"].lower() != full_name.lower():
        return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

    # Generate keycard in security service
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

    # Update room pin
    room_update_url = f"http://localhost:5006/rooms/{room_id}/update-pin"
    room_update_payload = {"room_pin": keycard_data["key_pin"]}
    room_response = requests.put(room_update_url, json=room_update_payload)

    if room_response.status_code != 200:
        print("Failed to update room pin:", room_response.json())

    # Update booking status to CHECKED-IN
    update_booking_url = f"http://localhost:5002/bookings/{booking_id}"
    update_payload = {"status": "CHECKED-IN"}
    requests.put(update_booking_url, json=update_payload)

    return jsonify({
        "code": 200,
        "message": "Self check-in successful. Use this PIN to access your room.",
        "keycard": keycard_data
    }), 200
