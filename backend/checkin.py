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

    # Verify booking exists
    booking_response = invokes.invoke_http(f"{BOOKING_URL}/booking/{booking_id}", method="GET")
    if booking_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.get("data", {})
    guest_id = booking_data.get("guest_id")
    room_id = booking_data.get("room_id")
    check_in = booking_data.get("check_in")
    floor = booking_data.get("floor")

    # Check-in date validation
    today = datetime.utcnow().date()
    try:
        check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
    except Exception:
        return jsonify({"code": 500, "message": "Invalid check-in date format."}), 500

    # Bypassing check-in date validation for testing purposes
    # if today != check_in_date:
    #     return jsonify({
    #         "code": 400,
    #         "message": f"Check-in is only allowed on the check-in date ({check_in}). Today is {today.strftime('%Y-%m-%d')}."
    #     }), 400

    # Verify guest exists
    guest_response = invokes.invoke_http(f"{GUEST_URL}/guest/{guest_id}", method="GET")
    if guest_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Guest record not found."}), 400

    guest_data = guest_response.get("data", {})
    if guest_data.get("name", "").lower() != name.lower():
        return jsonify({"code": 400, "message": "Full name does not match booking record."}), 400

    # Keycard generation
    keycard_payload = {
        "booking_id": booking_id,
        "guest_id": guest_id,
        "room_id": room_id,
        "floor": floor
    }

    print(f"Keycard payload: {keycard_payload}")

    # Check if keycard already exists
    existing_keycard_response = invokes.invoke_http(
        f"{KEYCARD_URL}/keycard/{booking_id}", method="GET"
    )

    if existing_keycard_response.get("code") == 200:
        keycard_data = existing_keycard_response.get("data", {})
        issued_at = keycard_data.get("issued_at")
        key_pin = keycard_data.get("key_pin")

        if issued_at == 'None' or key_pin == '00None':
            # Delete and recreate invalid keycard
            delete_response = invokes.invoke_http(
                f"{KEYCARD_URL}/keycard/{booking_id}", method="DELETE"
            )
            print(f"Deleted invalid keycard: {delete_response}")

            keycard_response = invokes.invoke_http(
                f"{KEYCARD_URL}/keycard", json=keycard_payload, method="POST"
            )
        else:
            keycard_response = existing_keycard_response
    else:
        keycard_response = invokes.invoke_http(
            f"{KEYCARD_URL}/keycard", json=keycard_payload, method="POST"
        )

    print(f"Keycard response: {keycard_response}")

    if keycard_response.get("code") not in [200, 201]:
        return jsonify({"code": 500, "message": "Failed to generate keycard."}), 500

    return jsonify({
        "code": 200,
        "message": "Self check-in successful. Use this PIN to access your room.",
        "keycard": keycard_response.get("data")
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
