from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# checkIn Function
@app.route("/checkin", methods=["POST"])
def checkin_guest():
    data = request.get_json()

    booking_id = data["booking_id"]
    user_id = data["user_id"]  #staff performing check-in

    #verify Booking Exists in `booking_service`
    booking_url = f"http://localhost:5002/bookings/{booking_id}"
    booking_response = requests.get(booking_url)

    if booking_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.json()["data"]
    room_id = booking_data["room_id"]
    customer_id = booking_data["customer_id"]

    # verify user exists in user_management
    user_url = f"http://localhost:5001/users/{user_id}/exists"
    user_response = requests.get(user_url)

    if user_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid staff user_id."}), 400
    
    #do user verification somehow (i honestly hv 0 clue)

    # generate keycard in security_service
    keycard_url = "http://localhost:5004/keycards"
    keycard_payload = {
        "booking_id": booking_id,
        "user_id": user_id,
        "customer_id": customer_id,
        "room_id": room_id
    }

    keycard_response = requests.post(keycard_url, json=keycard_payload)

    if keycard_response.status_code != 201:
        return jsonify({"code": 500, "message": "Failed to generate keycard."}), 500

    keycard_data = keycard_response.json()["data"]

    # update booking and room status to CHECKED-IN
    update_booking_url = f"http://localhost:5002/bookings/{booking_id}"
    update_payload = {"status": "CHECKED-IN"}
    update_response = requests.put(update_booking_url, json=update_payload)

    if update_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to update booking status."}), 500

    return jsonify({
        "code": 200,
        "message": "Guest checked in successfully.",
        "keycard": keycard_data
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
