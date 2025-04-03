from flask import Flask, request, jsonify
from flask_cors import CORS

import os, sys

import requests
from invokes import invoke_http
from datetime import datetime

app = Flask(__name__)
CORS(app)

roster_url = "http://localhost:4001/roster"
housekeepers_url = "http://localhost:4000/housekeepers"

@app.route("/housekeeping", methods=["POST"])
def assign_housekeeper():
    # Get room id
    room_id = request.json.get("room_id")

    # Get today's date
    today = datetime.now()
    # Format the date as YYYY-MM-DD
    date = today.strftime("%Y-%m-%d")
    date_json = {"date": date}

    # Create new task
    task_json = {
        "room_id": room_id,
        "date": date
    }
    task_result = invoke_http(roster_url, method='POST', json=task_json)

    # Update room availability
    room_url = "http://localhost:5006/rooms/" + str(room_id) + "/update-status"
    room_status = {"status": "CLEANING"}
    #room_result = invoke_http(room_url, method="PUT", json=room_status)

    return task_result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7001, debug=True)