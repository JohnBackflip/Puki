from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import requests
from datetime import datetime
import random
import string

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Room(db.Model):
    __tablename__ = "room"

    room_id = db.Column(db.String(36), primary_key=True)
    room_type = db.Column(db.Enum("Single", "Family", "PresidentialSuite"), nullable=False)
    status = db.Column(db.Enum("VACANT", "OCCUPIED", "CLEANING"), default="VACANT")
    
    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "status": self.status,
        }

with app.app_context():
    db.create_all()

#health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# API to create new room
@app.route("/rooms", methods=["POST"])
def create_room():
    data = request.get_json()

    if db.session.scalar(db.select(Room).filter_by(room_id=data["room_id"])):
        return jsonify({"code": 400, "message": "Room ID already exists."}), 400

    new_room = Room(
        room_id=data["room_id"],
        room_type=data["room_type"],
        status="VACANT"
    )

    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({"code": 201, "data": new_room.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating room: {str(e)}"}), 500

# API to get room by ID
@app.route("/rooms/<string:room_id>", methods=["GET"])
def get_room(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))

    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    return jsonify({"code": 200, "data": room.json()}), 200

# API to get rooms by status
@app.route("/rooms/status/<string:status>", methods=["GET"])
def get_rooms_by_status(status):
    rooms = db.session.scalars(db.select(Room).filter_by(status=status)).all()
    return jsonify({
        "code": 200,
        "data": {
            "rooms": [room.json() for room in rooms]
        }
    }), 200

#update room status
@app.route("/rooms/<string:room_id>/update-status", methods=["PUT"])
def update_room_status(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["VACANT", "OCCUPIED", "CLEANING", "COMPLETED"]:
        return jsonify({"code": 400, "message": "Invalid status value."}), 400

    room.status = new_status
    try:
        db.session.commit()
        return jsonify({"code": 200, "data": room.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": str(e)}), 500

# Room availability management
@app.route("/room/next-available/<string:room_type>", methods=["GET"])
def get_next_available_room(room_type):
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"code": 400, "message": "Date is required."}), 400
    
    check_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Get vacant rooms directly from database
    vacant_rooms = db.session.scalars(
        db.select(Room).filter_by(status="VACANT", room_type=room_type)
    ).all()

    if not vacant_rooms:
        return jsonify({"code": 404, "message": "No vacant rooms of this type."}), 404

    booking_url = environ.get("BOOKING_URL", "http://booking:5002")
    
    for room in vacant_rooms:
        booking_check_url = f"{booking_url}/bookings?room_id={room.room_id}&date={date_str}"
        try:
            booking_response = requests.get(booking_check_url)
            if booking_response.status_code == 404:
                return jsonify({"code": 200, "data": room.json()}), 200
        except requests.exceptions.RequestException:
            continue

    return jsonify({"code": 404, "message": "No available rooms of this type on the selected date."}), 404

# API to get available rooms
@app.route("/room/available", methods=["GET"])
def get_available_rooms():
    date_str = request.args.get("date")
    room_type = request.args.get("room_type")

    if not date_str:
        return jsonify({"code": 400, "message": "Date is required."}), 400

    check_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Get vacant rooms directly from database
    query = db.select(Room).filter_by(status="VACANT")
    if room_type:
        query = query.filter_by(room_type=room_type)
    
    vacant_rooms = db.session.scalars(query).all()

    if not vacant_rooms:
        return jsonify({"code": 404, "message": "No vacant rooms available."}), 404

    booking_url = environ.get("BOOKING_URL", "http://booking:5002")
    final_available_rooms = []

    for room in vacant_rooms:
        booking_check_url = f"{booking_url}/bookings?room_id={room.room_id}&date={date_str}"
        try:
            booking_response = requests.get(booking_check_url)
            if booking_response.status_code == 404:
                final_available_rooms.append(room.json())
        except requests.exceptions.RequestException:
            continue

    return jsonify({"code": 200, "data": {"rooms": final_available_rooms}}) if final_available_rooms else jsonify({"code": 404, "message": "No available rooms on this date."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
