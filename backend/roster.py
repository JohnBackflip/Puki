from datetime import datetime, date
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ 

app = Flask(__name__)
CORS(app)

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
    name = db.Column(db.String(50), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.PrimaryKeyConstraint('date', 'room_id', 'floor'),
    )

    def json(self):
        return {
            "date": self.date,
            "floor": self.floor,   
            "room_id": self.room_id,
            "housekeeper_id": self.housekeeper_id,
            "name": self.name,
            "completed": self.completed
        }
    
with app.app_context():
    db.create_all()

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Create a roster entry
@app.route("/roster", methods=["POST"])
def create_roster():
    data = request.get_json()

    # Convert the date string to a datetime object
    try:
        date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    # Check if the roster entry already exists for the given date, floor, and room_id
    existing_roster = Roster.query.filter_by(date=data["date"], floor=data["floor"], room_id=data["room_id"]).first()
    
    if existing_roster:
        return jsonify({"error": "Roster entry already exists for this date, floor, and room."}), 400

    try:
        # Create a new roster entry
        roster = Roster(
            date=data["date"],
            floor=data["floor"],
            room_id=data["room_id"],
            housekeeper_id=data["housekeeper_id"],
            name=data["name"],
            completed=data.get("completed", False)
        )

        db.session.add(roster)
        db.session.commit()
        return jsonify({"message": "Roster entry created successfully.", "data": roster.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error creating roster entry: {str(e)}"}), 500

# Get roster by housekeeper ID
@app.route("/roster/housekeeper/<int:housekeeper_id>", methods=["GET"])
def get_roster_by_housekeeper_id(housekeeper_id):
    roster_list = Roster.query.filter_by(housekeeper_id=housekeeper_id).all()
    if roster_list:
        return jsonify({"data": [r.json() for r in roster_list]}), 200
    return jsonify({"message": "No roster found for the provided housekeeper ID."}), 404

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

# New endpoint for assigning housekeeper by date & floor
@app.route("/roster/assign", methods=["GET"])
def get_housekeeper_by_date_and_floor():
    date = request.args.get("date")
    floor = request.args.get("floor")

    if not date or not floor:
        return jsonify({"code": 400, "message": "Missing date or floor parameter"}), 400

    roster_entry = Roster.query.filter_by(date=date, floor=int(floor)).first()
    if not roster_entry:
        return jsonify({"code": 404, "message": "No housekeeper assigned for this floor on the given date."}), 404

    return jsonify({
        "code": 200,
        "data": {
            "assigned_housekeeper": roster_entry.housekeeper_id
        }
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
