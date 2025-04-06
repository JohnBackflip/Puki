# complex microservice 
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import invokes
from os import environ

app = Flask(__name__)
CORS(app)

# Get URLs from environment variables
BOOKING_URL = environ.get('BOOKING_URL', 'http://localhost:5002')
GUEST_URL = environ.get('GUEST_URL', 'http://localhost:5011')
ROOM_URL = environ.get('ROOM_URL', 'http://localhost:5008')
KEYCARD_URL = environ.get('KEYCARD_URL', 'http://localhost:5012')
KEYCARD_HOST = environ.get('KEYCARD_HOST', 'keycard')
KEYCARD_PORT = environ.get('KEYCARD_PORT', '5012')

# health check
@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/checkin", methods=["POST"])
def self_checkin():
    data = request.get_json()
    booking_id = data.get("booking_id")
    name = data.get("name")

    # 1. Get booking
    booking_response = invokes.invoke_http(f"{BOOKING_URL}/booking/{booking_id}", method="GET")
    if booking_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking = booking_response["data"]
    guest_id = booking.get("guest_id")
    room_type = booking.get("room_type")
    check_in_date = booking.get("check_in")

    # 2. Validate today's date == check-in date
    today = datetime.utcnow().date()
    try:
        check_in_dt = datetime.strptime(check_in_date, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"code": 500, "message": "Invalid check-in date format."}), 500

    if today != check_in_dt:
        return jsonify({
            "code": 400,
            "message": f"Check-in only allowed on the check-in date ({check_in_dt}). Today is {today}."
        }), 400

    # 3. Get guest info and validate name
    guest_response = invokes.invoke_http(f"{GUEST_URL}/guest/{guest_id}", method="GET")
    if guest_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Guest not found."}), 400

    guest = guest_response["data"]
    if guest.get("name", "").strip().lower() != name.strip().lower():
        return jsonify({"code": 400, "message": "Guest name does not match booking record."}), 400

    # 4. Fetch available room by type
    room_response = invokes.invoke_http(f"{ROOM_URL}/room/next-available/{room_type}", method="GET")
    if room_response.get("code") != 200:
        return jsonify({"code": 400, "message": "No vacant room of this type available today."}), 400

    room = room_response["data"]
    room_id = room["room_id"]
    floor = room["floor"]

    # 5. Update booking to assign room
    update_booking_url = f"{BOOKING_URL}/booking/{booking_id}/assign-room"
    update_payload = {
        "room_id": room_id,
        "floor": floor
    }
    booking_update_response = invokes.invoke_http(update_booking_url, json=update_payload, method="PUT")
    if booking_update_response.get("code") != 200:
        return jsonify({"code": 500, "message": "Failed to update booking with room assignment."}), 500

    # 6. Mark room as OCCUPIED
    update_room_url = f"{ROOM_URL}/room/{room_id}/update-status"
    room_status_response = invokes.invoke_http(update_room_url, json={"status": "OCCUPIED"}, method="PUT")
    if room_status_response.get("code") != 200:
        return jsonify({"code": 500, "message": "Failed to update room status."}), 500

    # 7. Generate keycard
    keycard_payload = {
        "booking_id": booking_id,
        "guest_id": guest_id,
        "room_id": room_id
    }
    keycard_response = invokes.invoke_http(f"{KEYCARD_URL}/keycard", json=keycard_payload, method="POST")
    if keycard_response.get("code") not in [200, 201]:
        return jsonify({"code": 500, "message": "Keycard generation failed."}), 500

    return jsonify({
        "code": 200,
        "message": "Check-in successful. Keycard issued.",
        "data": {
            "room_id": room_id,
            "floor": floor,
            "keycard": keycard_response["data"]
        }
    }), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
