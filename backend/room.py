from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime
import random


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
    key_pin = db.Column(db.Integer, nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("VACANT", "OCCUPIED", "CLEANING"), default="VACANT")

    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "key_pin": self.key_pin,
            "floor": self.floor,
            "status": self.status
        }

with app.app_context():
    db.create_all()

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/room/create", methods=["POST"])
def create_room():
    data = request.get_json()
    room_id = str(data["room_id"]).zfill(3)
    floor = data["floor"]
    room_type = data["room_type"]

    if db.session.scalar(db.select(Room).filter_by(room_id=room_id)):
        return jsonify({"code": 400, "message": "Room ID already exists."}), 400

    new_room = Room(
        room_id=room_id,
        room_type=room_type,
        floor=floor,
        key_pin=random.randint(100000, 999999),
        status="VACANT"
    )

    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({"code": 201, "data": new_room.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating room: {str(e)}"}), 500

@app.route("/room/<string:room_id>", methods=["GET"])
def get_room(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404
    return jsonify({"code": 200, "data": room.json()}), 200

@app.route("/room/next-available/<string:room_type>", methods=["GET"])
def get_next_available_room(room_type):
    try:
        room = db.session.scalar(
            db.select(Room)
            .where(Room.room_type == room_type, Room.status == "VACANT")
            .limit(1)
        )
        if not room:
            return jsonify({"code": 404, "message": "No vacant room of this type."}), 404
        return jsonify({"code": 200, "data": room.json()}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"Error finding available room: {str(e)}"}), 500

@app.route("/room/type/<string:room_type>", methods=["GET"])
def get_rooms_by_type(room_type):
    valid_types = ["Single", "Family", "PresidentialSuite"]
    if room_type not in valid_types:
        return jsonify({"code": 400, "message": "Invalid room type."}), 400

    rooms = db.session.scalars(db.select(Room).filter_by(room_type=room_type)).all()
    if not rooms:
        return jsonify({"code": 404, "message": f"No rooms found for type {room_type}."}), 404

    return jsonify({"code": 200, "data": {"rooms": [room.json() for room in rooms]}}), 200

@app.route("/room", methods=["GET"])
def get_all_rooms():
    rooms = db.session.scalars(db.select(Room)).all()
    return jsonify({"code": 200, "data": {"rooms": [room.json() for room in rooms]}}), 200

@app.route("/room/available", methods=["POST"])
def update_room_availability():
    data = request.get_json()
    if not data or "date" not in data or "availability" not in data:
        return jsonify({"code": 400, "message": "Invalid request data."}), 400

    availability = data["availability"]
    try:
        single_rooms = db.session.scalars(db.select(Room).filter_by(room_type="Single")).all()
        double_rooms = db.session.scalars(db.select(Room).filter_by(room_type="Family")).all()
        family_rooms = db.session.scalars(db.select(Room).filter_by(room_type="PresidentialSuite")).all()

        for i, room in enumerate(single_rooms):
            room.status = "VACANT" if i < availability["single"] else "OCCUPIED"

        for i, room in enumerate(double_rooms):
            room.status = "VACANT" if i < availability["double"] else "OCCUPIED"

        for i, room in enumerate(family_rooms):
            room.status = "VACANT" if i < availability["family"] else "OCCUPIED"

        db.session.commit()

        return jsonify({
            "code": 200,
            "message": "Room availability updated successfully.",
            "data": availability
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room availability: {str(e)}"}), 500

@app.route("/room/<string:room_id>/update-status", methods=["PUT"])
def update_room_status(room_id):
    data = request.get_json()
    if not data or "status" not in data:
        return jsonify({"code": 400, "message": "Status is required."}), 400

    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    room.status = data["status"]
    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Room status updated successfully.", "data": room.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room status: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
