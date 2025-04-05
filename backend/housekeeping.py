from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import threading
import invokes  # Using invokes for HTTP requests
import time
from os import environ

app = Flask(__name__)
CORS(app)

# Get URLs from environment variables
ROOM_URL = environ.get('ROOM_URL', 'http://localhost:5008')
ROSTER_URL = environ.get('ROSTER_URL', 'http://localhost:5009')

# health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# assign housekeeper to room
@app.route("/housekeeping", methods=["POST"])
def housekeeping():
    try:
        data = request.get_json()
        room_id = data.get("room_id")
        floor = data.get("floor")
        if not room_id or not floor:
            return jsonify({"code": 400, "message": "room_id and floor are required"}), 400

        today = datetime.today().strftime("%Y-%m-%d")

        # 1. Fetch housekeeper assigned to the floor from Roster
        roster_response = invokes.invoke_http(
            f"{ROSTER_URL}/roster/assign",
            method="GET",
            params={"date": today, "floor": floor}
        )

        if roster_response.get("code") != 200:
            return jsonify({"code": 404, "message": "No housekeeper assigned for this floor today."}), 404

        assigned_housekeeper = roster_response.get("data", {}).get("assigned_housekeeper")

        # 2. Update room status to CLEANING via Room service
        room_response = invokes.invoke_http(
            f"{ROOM_URL}/room/status/{room_id}",
            method="PUT",
            json={"status": "CLEANING"}
        )

        if room_response.get("code") != 200:
            return jsonify({"code": 500, "message": "Failed to update room status"}), 500

        # 3. Simulate cleaning cycle in background
        thread = threading.Thread(target=simulate_cleaning_cycle, args=(room_id,))
        thread.start()

        return jsonify({
            "code": 200,
            "message": f"Room {room_id} marked for cleaning and assigned to {assigned_housekeeper}",
            "housekeeper": assigned_housekeeper
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": f"Unexpected error: {str(e)}"}), 500

# simulate cleaning cycle
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
