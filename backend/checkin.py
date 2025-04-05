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

# checkin with name
@app.route("/checkin", methods=["POST"])
def self_checkin():
    data = request.get_json()
    booking_id = data["booking_id"]
    name = data["name"]

    # Verify booking exists
    booking_url = f"{BOOKING_URL}/booking/{booking_id}"
    booking_response = invokes.invoke_http(booking_url, method="GET")

    if booking_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.get("data")
    guest_id = booking_data["guest_id"]
    room_id = booking_data["room_id"]
    check_in = booking_data["check_in"]

    # Check if today is the check-in date
    #today = datetime.strptime("2025-04-06", "%Y-%m-%d").date()  # Using the actual check-in date
    today = datetime.utcnow().date()  # Get current UTC date
    check_in = datetime.strptime(check_in, "%Y-%m-%d").date()
    if today != check_in:
        return jsonify({
            "code": 400, 
            "message": f"Check-in is only allowed on the check-in date ({check_in}). Today is {today.strftime('%Y-%m-%d')}."
        }), 400

    # Verify guest exists
    guest_url = f"{GUEST_URL}/guest/{guest_id}"
    guest_response = invokes.invoke_http(guest_url, method="GET")

    if guest_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Guest record not found."}), 400

    guest_data = guest_response.get("data")

    if guest_data["name"].lower() != name.lower():
        return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

    # Generate keycard
    keycard_payload = {
        "booking_id": booking_id,
        "guest_id": guest_id,
        "room_id": room_id,
        "floor": int(str(room_id)[0])  # Extract floor number from room_id (e.g., "501" -> 5)
    }
    print(f"Keycard URL: http://{KEYCARD_HOST}:{KEYCARD_PORT}/keycard")
    print(f"Keycard payload: {keycard_payload}")
    print(f"Payload types: booking_id={type(keycard_payload['booking_id'])}, guest_id={type(keycard_payload['guest_id'])}, floor={type(keycard_payload['floor'])}")
    
    # First check if a keycard already exists
    existing_keycard_response = invokes.invoke_http(f"http://{KEYCARD_HOST}:{KEYCARD_PORT}/keycard/{booking_id}", method="GET")
    
    if existing_keycard_response.status_code == 200:
        keycard_data = existing_keycard_response.json().get('data', {})
        if keycard_data.get('issued_at') == 'None' or keycard_data.get('key_pin') == '00None':
            # Keycard exists but is invalid - delete and recreate
            delete_response = invokes.invoke_http(f"http://{KEYCARD_HOST}:{KEYCARD_PORT}/keycard/{booking_id}", method="DELETE")
            print(f"Deleted invalid keycard: {delete_response.status_code}, {delete_response.text}")
            
            # Now create a new keycard
            keycard_response = invokes.invoke_http(f"http://{KEYCARD_HOST}:{KEYCARD_PORT}/keycard", json=keycard_payload, method="POST")
            print(f"Create keycard response: Status={keycard_response.status_code}, Response={keycard_response.text}")
        else:
            # Valid keycard already exists
            keycard_response = existing_keycard_response
    else:
        # No keycard exists, create a new one
        keycard_response = invokes.invoke_http(f"http://{KEYCARD_HOST}:{KEYCARD_PORT}/keycard", json=keycard_payload, method="POST")
    
    print(f"Keycard response: {keycard_response.status_code}, {keycard_response.text}")

    if keycard_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to generate keycard."}), 500

    return jsonify({
        "code": 200,
        "message": "Self check-in successful. Use this PIN to access your room.",
        "keycard": keycard_response.json().get("data")
    }), 200
    
@app.route("/validate-key-pin/<room_id>", methods=["GET"])
def validate_key_pin(room_id):
    # Get key_pin from Room microservice
    room_resp = invokes.invoke_http(f"{ROOM_URL}/rooms/{room_id}", method="GET")
    if room_resp.get("code") != 200:
        return jsonify({"code": 404, "message": "Room not found"}), 404
    room_key_pin = room_resp["data"].get("key_pin")

    # Get key_pin from Keycard microservice
    keycard_resp = invokes.invoke_http(f"{KEYCARD_URL}/keycard/{room_id}", method="GET")
    if keycard_resp.get("code") != 200:
        return jsonify({"code": 404, "message": "Keycard not found"}), 404
    keycard_key_pin = keycard_resp["data"].get("key_pin")

    # Compare key pins
    if room_key_pin == keycard_key_pin:
        return jsonify({"code": 200, "message": "✅ Key PIN matches"}), 200
    else:
        return jsonify({"code": 400, "message": "❌ Key PIN mismatch"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7002, debug=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
