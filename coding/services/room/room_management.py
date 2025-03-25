from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

room_mgmt_bp = Blueprint("room_mgmt_bp", __name__)

@room_mgmt_bp.route("/room-management/next-available/<string:room_type>", methods=["GET"])
def get_next_available_room(room_type):
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"code": 400, "message": "Date is required."}), 400
    # Get vacant rooms from our own endpoint
    room_service_url = "http://localhost:5006/rooms/status/VACANT"
    room_response = requests.get(room_service_url)
    if room_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to fetch rooms."}), 500
    vacant_rooms = room_response.json()["data"]["rooms"]
    # Filter by room_type
    vacant_rooms = [r for r in vacant_rooms if r["room_type"] == room_type]
    for room in vacant_rooms:
        # Check booking availability by calling the booking service
        booking_check_url = f"http://localhost:5002/bookings?room_id={room['room_id']}&date={date_str}"
        booking_response = requests.get(booking_check_url)
        if booking_response.status_code == 404:
            return jsonify({"code": 200, "data": room}), 200
    return jsonify({"code": 404, "message": "No available rooms of this type on the selected date."}), 404

@room_mgmt_bp.route("/room-management/available", methods=["GET"])
def get_available_rooms():
    date_str = request.args.get("date")
    room_type = request.args.get("room_type")
    if not date_str:
        return jsonify({"code": 400, "message": "Date is required."}), 400
    room_service_url = "http://localhost:5006/rooms/status/VACANT"
    room_response = requests.get(room_service_url)
    if room_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to fetch rooms."}), 500
    available_rooms = room_response.json()["data"]["rooms"]
    if room_type:
        available_rooms = [r for r in available_rooms if r["room_type"] == room_type]
    final_available_rooms = []
    for room in available_rooms:
        booking_check_url = f"http://localhost:5002/bookings?room_id={room['room_id']}&date={date_str}"
        booking_response = requests.get(booking_check_url)
        if booking_response.status_code == 404:
            final_available_rooms.append(room)
    if final_available_rooms:
        return jsonify({"code": 200, "data": {"rooms": final_available_rooms}})
    else:
        return jsonify({"code": 404, "message": "No available rooms on this date."}), 404

@room_mgmt_bp.route("/room-management/rooms", methods=["GET"])
def get_all_rooms():
    room_type = request.args.get("room_type")
    status = request.args.get("status")
    room_service_url = "http://localhost:5006/rooms"
    room_response = requests.get(room_service_url)
    if room_response.status_code != 200:
        return jsonify({"code": 500, "message": "Failed to fetch rooms."}), 500
    rooms = room_response.json()["data"]["rooms"]
    if room_type:
        rooms = [r for r in rooms if r["room_type"] == room_type]
    if status:
        rooms = [r for r in rooms if r["status"] == status]
    if rooms:
        return jsonify({"code": 200, "data": {"rooms": rooms}})
    else:
        return jsonify({"code": 404, "message": "No rooms found."}), 404
