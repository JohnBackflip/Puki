
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Roster model
class Roster(db.Model):
    __tablename__ = 'roster'

    date = db.Column(db.Date, nullable=False)
    floor = db.Column(db.Integer, nullable=True)
    room_id = db.Column(db.String(36), nullable=True)
    housekeeper_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('date', 'room_id', 'floor'),
    )

    def __init__(self, date, floor, room_id, housekeeper_id, completed=False):
        self.date = date
        self.floor = floor
        self.room_id = room_id
        self.housekeeper_id = housekeeper_id
        self.completed = completed

    def json(self):
        return {
            "date": self.date,
            "floor": self.floor,
            "room_id": self.room_id,
            "housekeeper_id": self.housekeeper_id,
            "completed": self.completed
        }

@app.route("/health")
def health():
    return {"status": "healthy"}

# Create a new roster entry
@app.route("/roster", methods=["POST"])
def create_roster():
    data = request.get_json()
    roster = Roster(**data)

    try:
        db.session.add(roster)
        db.session.commit()
        return jsonify({"message": "Roster entry created successfully.", "data": roster.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating roster entry: {str(e)}"}), 500

# Get roster by date
@app.route("/roster/<string:date>", methods=["GET"])
def get_roster_by_date(date):
    roster_list = Roster.query.filter_by(date=date).all()
    if roster_list:
        return jsonify({"data": [r.json() for r in roster_list]}), 200
    return jsonify({"message": "No roster found for the provided date."}), 404

# Update a roster entry (status change)
@app.route("/roster/<string:date>/<string:room_id>", methods=["PUT"])
def update_roster(date, room_id):
    roster = Roster.query.filter_by(date=date, room_id=room_id).first()
    if roster:
        data = request.get_json()
        if "completed" in data:
            roster.completed = data["completed"]

        db.session.commit()
        return jsonify({"message": "Roster entry updated successfully.", "data": roster.json()}), 200

    return jsonify({"message": "Roster entry not found."}), 404

# Delete a roster entry
@app.route("/roster/<string:date>/<string:room_id>", methods=["DELETE"])
def delete_roster(date, room_id):
    roster = Roster.query.filter_by(date=date, room_id=room_id).first()
    if roster:
        db.session.delete(roster)
        db.session.commit()
        return jsonify({"message": "Roster entry deleted successfully."}), 200

    return jsonify({"message": "Roster entry not found."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)