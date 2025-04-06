import random
import string
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import traceback

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Keycard model
class Keycard(db.Model):
    __tablename__ = "keycard"

    keycard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, nullable=False, unique=True)  # Links to a booking
    guest_id = db.Column(db.Integer, nullable=False)  # Customer using the key
    room_id = db.Column(db.String(5), nullable=False)
    key_pin = db.Column(db.Integer, nullable=False)  # 6-digit PIN
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Null if not expired

    def __init__(self, keycard_id, booking_id, guest_id, room_id, key_pin, issued_at, expires_at):
        self.keycard_id = keycard_id
        self.booking_id = booking_id
        self.guest_id = guest_id
        self.room_id = room_id  # Use the provided room_id directly
        self.key_pin = int(key_pin) if isinstance(key_pin, str) else key_pin
        self.issued_at = issued_at
        self.expires_at = expires_at

    def json(self):
        return {
            "keycard_id": self.keycard_id,
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "room_id": self.room_id,
            "key_pin": str(self.key_pin).zfill(6),  # Convert to 6-digit string
            "issued_at": str(self.issued_at),
            "expires_at": str(self.expires_at) if self.expires_at else None
        }

    # Generate pin
    @staticmethod
    def generate_pin():
        return random.randint(0, 999999)  # Return integer instead of string

# Auto-create table if not already present
with app.app_context():
    db.create_all()

# Health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Generate keycard
@app.route("/keycard", methods=["POST"])
def generate_keycard():
    try:
        data = request.get_json()
        print("Incoming payload:", data)

        # Basic validation
        required_fields = ["booking_id", "guest_id", "room_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"code": 400, "message": f"Missing field: {field}"}), 400

        # Check if a keycard already exists
        existing_keycard = db.session.scalar(
            db.select(Keycard).filter_by(booking_id=data["booking_id"])
        )
        if existing_keycard:
            return jsonify({"code": 400, "message": "Keycard already exists for this booking."}), 400

        # Get check-out date from booking service
        booking_url = environ.get("BOOKING_URL", "http://booking:5002")
        response = requests.get(f"{booking_url}/booking/{data['booking_id']}")

        if response.status_code != 200:
            return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

        booking_data = response.json()["data"]
        check_out = booking_data.get("check_out") or booking_data.get("check_out_date")

        if not check_out:
            return jsonify({"code": 500, "message": "Booking is missing check-out date."}), 500

        expires_at = datetime.strptime(check_out, "%Y-%m-%d") + timedelta(hours=15)

        new_keycard = Keycard(
            keycard_id=None,
            booking_id=data["booking_id"],
            guest_id=data["guest_id"],
            room_id=data["room_id"],
            key_pin=random.randint(0, 999999),
            issued_at=datetime.utcnow(),
            expires_at=expires_at
        )

        db.session.add(new_keycard)
        db.session.commit()

        return jsonify({"code": 201, "data": new_keycard.json()}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Failed to generate keycard: {str(e)}"}), 500
    

# Get pin for booking id (testing purposes)
@app.route("/keycard/<booking_id>", methods=["GET"])
def get_keycard(booking_id):
    try:
        # Convert booking_id to integer if it's a string
        booking_id = int(booking_id) if isinstance(booking_id, str) else booking_id
        
        keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))
        return jsonify({"code": 200, "data": keycard.json()}) if keycard else (jsonify({"code": 404, "message": "Keycard not found."}), 404)
    except Exception as e:
        print(f"Error in get_keycard: {str(e)}")
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

# Generates new pin for the booking
@app.route("/keycard/<int:booking_id>/renew", methods=["PUT"])
def renew_keycard(booking_id):
    keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))

    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    keycard.key_pin = str(random.randint(0, 999999)).zfill(6)
    keycard.issued_at = datetime.utcnow()
    keycard.expires_at = datetime.utcnow() + timedelta(days=1)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": keycard.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error renewing keycard: {str(e)}"}), 500

# Expire keycard (when user checks out)
@app.route("/keycard/<int:booking_id>/expire", methods=["PUT"])
def expire_keycard(booking_id):
    keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))

    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    keycard.expires_at = datetime.utcnow()

    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Keycard expired successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error expiring keycard: {str(e)}"}), 500

# Used when booking is extended
@app.route("/keycard/<int:booking_id>/update-expiry", methods=["PUT"])
def update_keycard_expiry(booking_id):
    data = request.get_json()
    keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))

    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    # Keep the same key PIN
    keycard.expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%d %H:%M:%S")

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": keycard.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating keycard expiry: {str(e)}"}), 500

# Delete keycard by booking ID
@app.route("/keycard/<booking_id>", methods=["DELETE"])
def delete_keycard(booking_id):
    """Delete a keycard by booking ID."""
    try:
        # Convert booking_id to integer if it's a string
        booking_id = int(booking_id) if isinstance(booking_id, str) else booking_id
        
        keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))
        
        if not keycard:
            return jsonify({"code": 404, "message": "Keycard not found."}), 404
        
        # Delete the keycard
        db.session.delete(keycard)
        db.session.commit()
        
        return jsonify({"code": 200, "message": "Keycard deleted successfully."}), 200
    
    except Exception as e:
        print(f"Error in delete_keycard: {str(e)}")
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5012, debug=True)