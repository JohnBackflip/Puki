from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import requests
from datetime import datetime

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
    availability = db.Column(db.Enum("VACANT", "OCCUPIED", "CLEANING"), default="VACANT")
    
    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "key_pin": self.key_pin,
            "floor": self.floor,
            "availability": self.availability
        }
    
with app.app_context():
    db.create_all()

# health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Create new room
@app.route("/room/create", methods=["POST"])
def create_room():
    data = request.get_json()

   # Extract room_id, floor, and room_type from the incoming data
    room_id = str(data["room_id"]).zfill(3)  # Ensuring room_id is 3 digits (e.g., 901 -> "901")
    floor = data["floor"]
    room_type = data["room_type"]

    # Check if the room_id already exists
    if db.session.scalar(db.select(Room).filter_by(room_id=room_id)):
        return jsonify({"code": 400, "message": "Room ID already exists."}), 400

    # Create the new room using the provided room_id, room_type, and floor
    new_room = Room(
        room_id=room_id,
        room_type=room_type,
        floor=floor,
        availability="VACANT"
    )
    
    try:
        db.session.add(new_room)
        db.session.commit()
        return jsonify({"code": 201, "data": new_room.json()}), 201
    except Exception as e:
        db.session.rollback()
        print("Error creating room:", str(e))
        return jsonify({"code": 500, "message": "Error creating room."}), 500

# get room by ID
@app.route("/room/<string:room_id>", methods=["GET"])
def get_room(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))

    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    return jsonify({"code": 200, "data": room.json()}), 200

# get rooms by status
@app.route("/room/availability/<string:availability>", methods=["GET"])
def get_rooms_by_availability(availability):
    rooms = db.session.scalars(db.select(Room).filter_by(availability=availability)).all()
    return jsonify({
        "code": 200,
        "data": {
            "rooms": [room.json() for room in rooms]
        }
    }), 200

# get rooms by type
@app.route("/room/type/<string:room_type>", methods=["GET"])
def get_rooms_by_type(room_type):
    valid_types = ["Single", "Family", "PresidentialSuite"]
    
    if room_type not in valid_types:
        return jsonify({"code": 400, "message": "Invalid room type."}), 400

    rooms = db.session.scalars(db.select(Room).filter_by(room_type=room_type)).all()

    if not rooms:
        return jsonify({"code": 404, "message": f"No rooms found for type {room_type}."}), 404

    return jsonify({"code": 200, "data": {"rooms": [room.json() for room in rooms]}}), 200

# Get all rooms
@app.route("/room", methods=["GET"])
def get_all_rooms():
    rooms = db.session.scalars(db.select(Room)).all()
    return jsonify({
        "code": 200,
        "data": {
            "rooms": [room.json() for room in rooms]
        }
    }), 200

# Update room availability
@app.route("/room/available", methods=["POST"])
def update_room_availability():
    data = request.get_json()
    
    # Validate request data
    if not data or "date" not in data or "availability" not in data:
        return jsonify({"code": 400, "message": "Invalid request data."}), 400
        
    date_str = data["date"]
    availability = data["availability"]
    
    try:
        # Get all rooms by type
        single_rooms = db.session.scalars(db.select(Room).filter_by(room_type="Single")).all()
        double_rooms = db.session.scalars(db.select(Room).filter_by(room_type="Family")).all()
        family_rooms = db.session.scalars(db.select(Room).filter_by(room_type="PresidentialSuite")).all()

        # Update Single rooms
        for i, room in enumerate(single_rooms):
            if i < availability["single"]:
                room.availability = "VACANT"
            else:
                room.availability = "OCCUPIED"
        
        # Update Double rooms
        for i, room in enumerate(double_rooms):
            if i < availability["double"]:
                room.availability = "VACANT"
            else:
                room.availability = "OCCUPIED"
                
        # Update Family rooms
        for i, room in enumerate(family_rooms):
            if i < availability["family"]:
                room.availability = "VACANT"
            else:
                room.availability = "OCCUPIED"
        
        # Commit the changes to the database
        db.session.commit()
        
        return jsonify({
            "code": 200,
            "message": "Room availability updated successfully.",
            "data": {
                "date": date_str,
                "availability": availability
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room availability: {str(e)}"}), 500

# Update room status - DONT REMOVE THIS
@app.route("/room/<string:room_id>/update-status", methods=["PUT"])
def update_room_status(room_id):
    data = request.get_json()
    
    # Validate that the status is provided
    if not data or "status" not in data:
        return jsonify({"code": 400, "message": "Status is required."}), 400

    # Fetch the room from the database
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))

    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    # Update the room's status
    room.availability = data["status"]

    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Room status updated successfully.", "data": room.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room status: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
