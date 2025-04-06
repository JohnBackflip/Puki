from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import threading
import invokes 
import time
from os import environ

app = Flask(__name__)
CORS(app)

# Get URLs from environment variables
ROOM_URL = environ.get('ROOM_URL', 'http://localhost:5008')
ROSTER_URL = environ.get('ROSTER_URL', 'http://localhost:5009')
HOUSEKEEPER_URL = environ.get('HOUSEKEEPER_URL', 'http://localhost:5014')

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
        if not room_id or floor is None:
            return jsonify({"code": 400, "message": "room_id and floor are required"}), 400

        today = datetime.today().strftime("%Y-%m-%d")

        # 1. Fetch housekeeper on the same floor as room from Housekeeper
        housekeeper_response = invokes.invoke_http(
            f"{HOUSEKEEPER_URL}/housekeeper/floor/{floor}",
            method="GET"
        )

        if housekeeper_response.get("code") != 200:
            return jsonify({"code": 404, "message": f"No housekeeper available on floor {floor}."}), 404

        housekeeper_data = housekeeper_response.get("data", {})
        assigned_housekeeper = housekeeper_data.get("housekeeper_id")
        housekeeper_floor = housekeeper_data.get("floor")

        if not assigned_housekeeper:
            return jsonify({"code": 404, "message": f"No housekeeper found for floor {floor}."}), 404

        # 2. Fetch actual floor of the room from Room service to validate
        room_details_response = invokes.invoke_http(
            f"{ROOM_URL}/room/{room_id}",
            method="GET"
        )

        if room_details_response.get("code") != 200:
            return jsonify({"code": 404, "message": "Room not found."}), 404

        room_data = room_details_response.get("data", {})
        actual_room_floor = room_data.get("floor")

        if actual_room_floor != housekeeper_floor:
            return jsonify({
                "code": 400,
                "message": f"Housekeeper is not on floor {actual_room_floor}. Floor mismatch."
            }), 400
        
        # 3. Add the housekeeper assignment to the Roster
        roster_payload = {
            "housekeeper_id": assigned_housekeeper,
            "floor": housekeeper_floor,
            "date": today
        }
        print(f"DEBUG: Adding to Roster: {roster_payload}")
        try:
            roster_response = invokes.invoke_http(
                f"{ROSTER_URL}/roster/new",
                method="POST",
                json=roster_payload
            )
            print(f"DEBUG: Roster insert response: {roster_response}")
            if roster_response.get("code") != 201:
                print(f"[WARN] Roster insertion failed: {roster_response}")
        except Exception as e:
            print(f"[ERROR] Failed to update roster: {str(e)}")
        
        # 4. Update room status to CLEANING via Room service
        room_update_url = f"{ROOM_URL}/room/{room_id}/update-status"
        print(f"DEBUG: Updating room status at URL: {room_update_url}")
        try:
            room_response = invokes.invoke_http(
                room_update_url,
                method="PUT",
                json={"status": "CLEANING"}
            )
            print(f"DEBUG: Room update response: {room_response}")
            
            if not isinstance(room_response, dict):
                print(f"DEBUG: Room response is not a dict: {room_response}")
                return jsonify({"code": 400, "message": "Failed to update room status - invalid response format"}), 400
                
            if room_response.get("code") != 200:
                print(f"DEBUG: Room update failed with code: {room_response.get('code')} - {room_response.get('message', 'No error message')}")
                return jsonify({"code": 500, "message": f"Failed to update room status: {room_response.get('message', 'Unknown error')}"}), 500
                
        except Exception as e:
            print(f"DEBUG: Exception updating room status: {str(e)}")
            return jsonify({"code": 500, "message": "Error updating room status."}), 500

        # 3. Simulate cleaning cycle in background
        thread = threading.Thread(target=simulate_cleaning_cycle, args=(room_id,))
        thread.start()

        return jsonify({
            "code": 200,
            "message": f"Room {room_id} marked for cleaning and assigned to housekeeper {assigned_housekeeper}",
            "housekeeper": assigned_housekeeper
        }), 200

    except Exception as e:
        return jsonify({"code": 500, "message": "An unexpected error occurred."}), 500

# simulate cleaning cycle
def simulate_cleaning_cycle(room_id):
    time.sleep(10)
    print(f"[INFO] Cleaning completed for room {room_id}")

    try:
        room_status_response = invokes.invoke_http(
            f"{ROOM_URL}/room/{room_id}/update-status",
            method="PUT",
            json={"status": "COMPLETED"}
        )
        if room_status_response.get("code") != 200:
            print(f"[ERROR] Failed to set COMPLETED status for room {room_id}")
    except Exception as e:
        print(f"[ERROR] Failed to set COMPLETED status: {str(e)}")

    time.sleep(5)

    try:
        booking_response = invokes.invoke_http(f"{ROOM_URL}/booking/active/{room_id}", method="GET")
        final_status = "OCCUPIED" if booking_response.get("code") == 200 else "VACANT"
        print(f"[INFO] Final status for room {room_id}: {final_status}")
        room_status_response = invokes.invoke_http(
            f"{ROOM_URL}/room/{room_id}/update-status",
            method="PUT",
            json={"status": final_status}
        )
        if room_status_response.get("code") != 200:
            print(f"[ERROR] Failed to set final status for room {room_id}")
    except Exception as e:
        print(f"[ERROR] Failed to set final status: {str(e)}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
