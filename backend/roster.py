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

    date = db.Column(db.Date, primary_key=True)
    room_id = db.Column(db.String(36), primary_key=True)
    floor = db.Column(db.Integer, nullable=False)
    housekeeper_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)

    def json(self):
        return {
            "date": self.date,
            "room_id": self.room_id,
            "floor": self.floor,
            "housekeeper_id": self.housekeeper_id,
            "completed": self.completed
        }
    
with app.app_context():
    db.create_all()

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Get all roster entries
@app.route("/roster", methods=["GET"])
def get_all_roster():
    roster_list = Roster.query.all()
    if roster_list:
        return jsonify({"code": 200, "data": [r.json() for r in roster_list]}), 200
    return jsonify({"code": 404, "message": "No roster found."}), 404

# Create a roster entry
@app.route("/roster/new", methods=["POST"])
def create_roster():
    data = request.get_json()
    try:
        room_id = data["room_id"]
        housekeeper_id = data["housekeeper_id"]
        date_str = data["date"]

        # Parse date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return jsonify({"code": 400, "error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Derive floor from room_id
        floor = int(str(room_id)[0])
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check if this roster entry already exists
        existing = Roster.query.filter_by(date=date_obj, room_id=room_id).first()

        if existing:
            return jsonify({"code": 400, "error": "Roster entry already exists."}), 400

        # Create new roster entry
        new_entry = Roster(
            date=date_obj,
            room_id=room_id,
            floor=floor,
            housekeeper_id=housekeeper_id,
            completed=False
        )
        db.session.add(new_entry)
        db.session.commit()

        return jsonify({
            "code": 201,
            "message": "Roster entry created successfully.",
            "data": new_entry.json()
        }), 201

    except KeyError as e:
        return jsonify({"code": 400, "error": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Roster creation failed: {str(e)}")
        return jsonify({"code": 500, "error": "Internal server error."}), 500


# Get roster by housekeeper ID
@app.route("/roster/housekeeper/<int:housekeeper_id>", methods=["GET"])
def get_roster_by_housekeeper_id(housekeeper_id):
    roster_list = Roster.query.filter_by(housekeeper_id=housekeeper_id).all()
    if roster_list:
        return jsonify({"code": 200, "data": [r.json() for r in roster_list]}), 200
    return jsonify({"code": 404, "message": "No roster found for the provided housekeeper ID."}), 404

# Get roster by date
@app.route("/roster/<string:date>", methods=["GET"])
def get_roster_by_date(date):
    try:
        # Convert string date to datetime.date object
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({
            "code": 400,
            "message": "Invalid date format. Please use YYYY-MM-DD."
        }), 400

    roster_list = Roster.query.filter_by(date=date_obj).all()
    
    if roster_list:
        return jsonify({
            "code": 200,
            "data": {
                "roster": [r.json() for r in roster_list]
            }
        }), 200
    
    return jsonify({
        "code": 404,
        "message": "No roster found for the provided date."
    }), 404

# Update a roster entry (status change)
@app.route("/roster/<string:date>/<string:room_id>", methods=["PUT"])
def update_roster(date, room_id):
    roster = Roster.query.filter_by(date=date, room_id=room_id).first()
    if roster:
        data = request.get_json()
        if "completed" in data:
            roster.completed = data["completed"]

        db.session.commit()
        return jsonify({"code": 200, "message": "Roster entry updated successfully.", "data": roster.json()}), 200

    return jsonify({"code": 404, "message": "Roster entry not found."}), 404

# Delete a roster entry
@app.route("/roster/<string:date>/<string:room_id>", methods=["DELETE"])
def delete_roster(date, room_id):
    roster = Roster.query.filter_by(date=date, room_id=room_id).first()
    if roster:
        db.session.delete(roster)
        db.session.commit()
        return jsonify({"code": 200, "message": "Roster entry deleted successfully."}), 200

    return jsonify({"code": 404, "message": "Roster entry not found."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5009, debug=True)
