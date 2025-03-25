from flask import Blueprint, request, jsonify
from room.models import Room
from room.database import db

room_bp = Blueprint("room_bp", __name__)

@room_bp.route("/rooms", methods=["POST"])
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

@room_bp.route("/rooms/<string:room_id>", methods=["GET"])
def get_room(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404
    return jsonify({"code": 200, "data": room.json()}), 200

@room_bp.route("/rooms/<string:room_id>/update-status", methods=["PUT"])
def update_room_status(room_id):
    data = request.get_json()
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    if data["status"] not in ["VACANT", "OCCUPIED", "UNAVAI"]:
        return jsonify({"code": 400, "message": "Invalid status update."}), 400

    room.status = data["status"]

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": room.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room status: {str(e)}"}), 500

@room_bp.route("/rooms/<string:room_id>/pin", methods=["GET"])
def get_room_pin(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404
    return jsonify({"code": 200, "data": {"room_id": room.room_id, "room_pin": room.room_pin}}), 200

@room_bp.route("/rooms/<string:room_id>/update-pin", methods=["PUT"])
def update_room_pin(room_id):
    data = request.get_json()
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))
    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    room.room_pin = data.get("room_pin")
    try:
        db.session.commit()
        return jsonify({"code": 200, "data": room.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating room pin: {str(e)}"}), 500

# Additional endpoint: Get rooms by status (needed for management endpoints)
@room_bp.route("/rooms/status/<string:status>", methods=["GET"])
def get_rooms_by_status(status):
    rooms = db.session.scalars(db.select(Room).filter_by(status=status)).all()
    if not rooms:
        return jsonify({"code": 404, "message": "No rooms found with the given status."}), 404
    return jsonify({"code": 200, "data": {"rooms": [room.json() for room in rooms]}}), 200
