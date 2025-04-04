from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import threading
import invokes  # Using invokes for HTTP requests
import time
from os import environ

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# Get URLs from environment variables
ROOM_URL = environ.get('ROOM_URL', 'http://localhost:5008')
ROSTER_URL = environ.get('ROSTER_URL', 'http://localhost:5009')

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/clean", methods=["POST"])
def clean_room():
    data = request.get_json()
    room_id = data["room_id"]

    # verify room exists
    room_url = f"{ROOM_URL}/rooms/{room_id}"
    room_response = invokes.invoke_http(room_url, method="GET")

    if room_response.get("code") != 200:
        return jsonify({"code": 400, "message": "Invalid room ID."}), 400

    # get available housekeepers
    roster_url = f"{ROSTER_URL}/housekeepers/available"
    roster_response = invokes.invoke_http(roster_url, method="GET")

    if roster_response.get("code") != 200:
        return jsonify({"code": 500, "message": "Failed to get available housekeepers."}), 500

    housekeepers = roster_response.get("data")
    if not housekeepers:
        return jsonify({"code": 503, "message": "No housekeepers available at the moment."}), 503

    # assign housekeeper
    housekeeper = housekeepers[0]
    assign_url = f"{ROSTER_URL}/housekeepers/{housekeeper['id']}/assign"
    assign_payload = {"room_id": room_id}
    assign_response = invokes.invoke_http(assign_url, method="POST", json=assign_payload)

    if assign_response.get("code") != 200:
        return jsonify({"code": 500, "message": "Failed to assign housekeeper."}), 500

    return jsonify({
        "code": 200,
        "message": "Housekeeper assigned successfully",
        "housekeeper": housekeeper
    }), 200

def simulate_cleaning_cycle(room_id):
    # Wait to simulate cleaning (e.g., 10 seconds)
    time.sleep(10)
    print(f"[INFO] Cleaning completed for room {room_id}")

    # Update room status to COMPLETED
    try:
        room_status_response = invokes.invoke_http(f"{ROOM_URL}/rooms/{room_id}/update-status", method="PUT", json={"status": "COMPLETED"})
        if room_status_response.get("code") != 200:
            print(f"[ERROR] Failed to set COMPLETED status for room {room_id}")
    except Exception as e:
        print(f"[ERROR] Failed to set COMPLETED status: {str(e)}")

    # Wait before determining final room status (e.g., 5 seconds)
    time.sleep(5)

    try:
        # Query if room is occupied
        booking_response = invokes.invoke_http(f"{ROOM_URL}/bookings/active/{room_id}", method="GET")
        if booking_response.get("code") == 200:
            final_status = "OCCUPIED"
        else:
            final_status = "VACANT"

        print(f"[INFO] Final status for room {room_id}: {final_status}")
        room_status_response = invokes.invoke_http(f"{ROOM_URL}/rooms/{room_id}/update-status", method="PUT", json={"status": final_status})
        if room_status_response.get("code") != 200:
            print(f"[ERROR] Failed to set final status for room {room_id}")
    except Exception as e:
        print(f"[ERROR] Failed to set final status: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
