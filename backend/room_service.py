from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
CORS(app)

# database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)

class Room(db.Model):
    __tablename__ = "room"

    room_id = db.Column(db.String(36), primary_key=True)
    room_type = db.Column(db.Enum("Single", "Double", "Family", "PresidentialRooms"), nullable=False)
    status = db.Column(db.Enum("VACANT", "OCCUPIED", "UNAVAI"), default="VACANT")
    room_pin = db.Column(db.String(6), default=None)

    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "status": self.status,
            "room_pin": self.room_pin
        }


with app.app_context():
    db.create_all()


# make new room
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


# get room id 
@app.route("/rooms/<string:room_id>", methods=["GET"])
def get_room(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))

    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    return jsonify({"code": 200, "data": room.json()}), 200


# update room status
@app.route("/rooms/<string:room_id>/update-status", methods=["PUT"])
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


# get room pin
@app.route("/rooms/<string:room_id>/pin", methods=["GET"])
def get_room_pin(room_id):
    room = db.session.scalar(db.select(Room).filter_by(room_id=room_id))

    if not room:
        return jsonify({"code": 404, "message": "Room not found."}), 404

    return jsonify({"code": 200, "data": {"room_id": room.room_id, "room_pin": room.room_pin}}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=True)
