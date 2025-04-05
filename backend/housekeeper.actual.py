from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ

app = Flask(__name__)
CORS(app)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL", "sqlite:///housekeepers.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Housekeeper Model
class Housekeeper(db.Model):
    __tablename__ = "housekeeper"

    housekeeper_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, nullable=False)

    def json(self):
        return {
            "housekeeper_id": self.housekeeper_id,
            "name": self.name,
            "floor": self.floor
        }

# Create the table
with app.app_context():
    db.create_all()

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Get all housekeepers
@app.route("/housekeeper", methods=["GET"])
def get_all_housekeepers():
    housekeepers = Housekeeper.query.all()
    return jsonify([h.json() for h in housekeepers]), 200

# Create a new housekeeper
@app.route("/housekeeper", methods=["POST"])
def create_housekeeper():
    data = request.get_json()
    name = data.get("name")
    floor = data.get("floor")

    if not name or floor is None:
        return jsonify({"code": 400, "message": "Name and floor are required."}), 400

    new_housekeeper = Housekeeper(name=name, floor=floor)

    try:
        db.session.add(new_housekeeper)
        db.session.commit()
        return jsonify({"code": 201, "data": new_housekeeper.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

# Get housekeeper by floor 
@app.route("/housekeeper/floor/<int:floor>", methods=["GET"])
def get_housekeeper_by_floor(floor):
    housekeeper_entry = Housekeeper.query.filter_by(floor=floor).first()
    
    if not housekeeper_entry:
        return jsonify({"code": 404, "message": "No housekeeper assigned for this floor."}), 404

    return jsonify({
        "code": 200,
        "data": {
            "housekeeper_id": housekeeper_entry.housekeeper_id,
            "name": housekeeper_entry.name,
            "floor": housekeeper_entry.floor
        }
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5014, debug=True)
