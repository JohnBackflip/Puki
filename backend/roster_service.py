from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)

CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = (
     environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)


class FloorRoster(db.Model):
    __tablename__ = "floor_roster"

    date = db.Column(db.Date, primary_key=True)
    floor = db.Column(db.Integer, primary_key=True)
    assigned_housekeeper = db.Column(db.String(64), nullable=False)

    def __init__(self, date, floor, assigned_housekeeper):
        self.date = date
        self.floor = floor
        self.assigned_housekeeper = assigned_housekeeper

    def json(self):
        return {
            "date": self.date,
            "floor": self.floor,
            "assigned_housekeeper": self.assigned_housekeeper,
        }

class RoomsRoster(db.Model):
    __tablename__ = "rooms_roster"

    date = db.Column(db.Date, primary_key=True)
    room_id = db.Column(db.Integer, primary_key=True)
    completed = db.Column(db.Boolean, nullable=False)

    def __init__(self, date, room_id, completed):
        self.date = date
        self.room_id = room_id
        self.completed = completed

    def json(self):
        return {
            "date": self.date,
            "room_id": self.room_id,
            "completed": self.completed,
        }

@app.route("/roster/<string:date>")
def get_roster_today(date):

    # Refreshes to get latest data
    db.session.expire_all()

    rosterlist = FloorRoster.query.filter_by(date=date).all()
    roomslist = RoomsRoster.query.filter_by(date=date).all()

    #rosterlist = db.session.scalars(db.select(FloorRoster).filter_by(date=date)).all()
    #roomslist = db.session.scalars(db.select(RoomsRoster).filter_by(date=date)).all()

    # Compiling the all assigned rooms into a single list for each housekeeper
    results = []
    for roster in rosterlist:
        roster_json = roster.json()
        roster_json["rooms"] = []
        for room in roomslist:
            room_json = room.json()
            room_floor = int(str(room_json["room_id"])[:-2])
            if room_floor == roster_json["floor"]:
                roster_json["rooms"].append(room_json["room_id"])
                #roomslist.remove(room)
        results.append(roster_json)

    if len(results):
        return jsonify(
            {
                "code": 200,
                "data": {"roster": [roster for roster in results]},
            }
        )
    return jsonify({"code": 404, "message": "There are no tasks."}), 404

@app.route("/roster", methods=["POST"])
def add_task():
    room_id = request.json.get('room_id')
    date = request.json.get('date')
    task = RoomsRoster(date, room_id, False)
    try:
        db.session.add(task)
        db.session.commit()
        return jsonify(
            {
                "code": 200,
                "message": "Task was added successfully."
            }
        )
    except Exception as e:
        print("Error: {}".format(str(e)))
        return jsonify(
            {
                "code": 500,
                "message": "An error occurred while adding the task. " + str(e)
            }
        ), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
