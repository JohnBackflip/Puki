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

        if not room_id:
            return jsonify({"code": 400, "message": "room_id is required."}), 400

        # Derive floor from room_id
        try:
            floor = int(str(room_id)[0])
        except (TypeError, ValueError):
            return jsonify({"code": 400, "message": "Invalid room_id format."}), 400

        today = datetime.today().strftime("%Y-%m-%d")

        # Check today's roster for someone already assigned to this floor
        assigned_housekeeper = None
        roster_response = invokes.invoke_http(f"{ROSTER_URL}/roster/{today}", method="GET")

        if roster_response.get("code") == 200:
            for entry in roster_response["data"]["roster"]:
                if entry["floor"] == floor:
                    assigned_housekeeper = entry["housekeeper_id"]
                    print(f"[INFO] Reusing housekeeper {assigned_housekeeper} for floor {floor}")
                    break

        # If none yet, fetch housekeeper for this floor 
        if not assigned_housekeeper:
            housekeeper_response = invokes.invoke_http(
                f"{HOUSEKEEPER_URL}/housekeeper/floor/{floor}",
                method="GET"
            )

            if housekeeper_response.get("code") == 200:
                assigned_housekeeper = housekeeper_response["data"]["housekeeper_id"]
            else:
                print(f"[INFO] No housekeeper found on floor {floor}, creating one...")
                create_response = invokes.invoke_http(
                    f"{HOUSEKEEPER_URL}/housekeeper",
                    method="POST",
                    json={
                        "name": f"Auto-HK-Floor-{floor}",
                        "floor": floor
                    }
                )

                if create_response.get("code") != 201:
                    return jsonify({"code": 500, "message": f"Failed to auto-create housekeeper for floor {floor}."}), 500

                assigned_housekeeper = create_response["data"]["housekeeper_id"]
                print(f"[INFO] Auto-assigned new housekeeper ID {assigned_housekeeper} to floor {floor}")

        # Confirm room exists
        room_response = invokes.invoke_http(f"{ROOM_URL}/room/{room_id}", method="GET")
        if room_response.get("code") != 200:
            return jsonify({"code": 404, "message": "Room not found."}), 404

        room_data = room_response["data"]
        actual_room_floor = room_data.get("floor")

        if actual_room_floor != floor:
            return jsonify({
                "code": 400,
                "message": f"Room floor mismatch. Expected floor {floor}, but got {actual_room_floor}"
            }), 400

        # Create roster entry
        roster_payload = {
            "housekeeper_id": assigned_housekeeper,
            "room_id": room_id,
            "floor": floor,
            "date": today
        }

        print(f"[DEBUG] Adding to Roster: {roster_payload}")
        try:
            roster_create = invokes.invoke_http(
                f"{ROSTER_URL}/roster/new", method="POST", json=roster_payload
            )
            if roster_create.get("code") != 201:
                print(f"[WARN] Failed to insert roster: {roster_create}")
        except Exception as e:
            print(f"[ERROR] Failed to insert roster: {str(e)}")

        # Update room status to CLEANING
        update_response = invokes.invoke_http(
            f"{ROOM_URL}/room/{room_id}/update-status",
            method="PUT",
            json={"status": "CLEANING"}
        )
        if update_response.get("code") != 200:
            return jsonify({"code": 500, "message": "Failed to update room status."}), 500

        # Start simulated cleaning
        thread = threading.Thread(target=simulate_cleaning_cycle, args=(room_id,))
        thread.start()

        return jsonify({
            "code": 201,
            "message": f"Room {room_id} marked for cleaning and assigned to housekeeper {assigned_housekeeper}",
            "housekeeper": assigned_housekeeper
        }), 201

    except Exception as e:
        print("[ERROR] Housekeeping failure:", str(e))
        return jsonify({"code": 500, "message": "Unexpected error during housekeeping."}), 500


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
