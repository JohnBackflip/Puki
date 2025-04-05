import random
import string
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

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
    key_pin = db.Column(db.Integer, nullable=False, unique=True)  # 6-digit PIN
    floor = db.Column(db.Integer, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Null if not expired

    def __init__(self, keycard_id, booking_id, guest_id, room_id, key_pin, floor, issued_at, expires_at):
        self.keycard_id = keycard_id
        self.booking_id = booking_id
        self.guest_id = guest_id
        self.room_id = room_id  # Use the provided room_id directly
        self.key_pin = int(key_pin) if isinstance(key_pin, str) else key_pin
        self.floor = floor
        self.issued_at = issued_at
        self.expires_at = expires_at

    def json(self):
        return {
            "keycard_id": self.keycard_id,
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "room_id": self.room_id,
            "key_pin": str(self.key_pin).zfill(6),  # Convert to 6-digit string
            "floor": self.floor,
            "issued_at": str(self.issued_at),
            "expires_at": str(self.expires_at) if self.expires_at else None
        }

    # Generate pin
    @staticmethod
    def generate_pin():
        return random.randint(0, 999999)  # Return integer instead of string

    @staticmethod
    def generate_room_id(floor):
        # Find the last room on the floor to get the next available room number
        last_room = db.session.query(Keycard).filter_by(floor=floor).order_by(Keycard.room_id.desc()).first()
        if last_room:
            last_room_number = int(last_room.room_id)
            new_room_number = str(last_room_number + 1)
        else:
            new_room_number = str(floor) + "01"
        return new_room_number

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
        print("Received data:", data)  # Add logging
        if not data:
            return jsonify({"code": 400, "message": "No JSON data received"}), 400

        print("Data types:", {k: type(v) for k, v in data.items()})  # Add logging

        # Convert booking_id to integer if it's a string
        if isinstance(data.get("booking_id"), str):
            data["booking_id"] = int(data["booking_id"])
        if isinstance(data.get("guest_id"), str):
            data["guest_id"] = int(data["guest_id"])
        if isinstance(data.get("floor"), str):
            data["floor"] = int(data["floor"])
            
        print("Converted data:", data)  # Add detailed logging

        required_fields = ["booking_id", "guest_id", "room_id", "floor"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            print(f"Missing fields: {missing_fields}")  # Add detailed logging
            return jsonify({"code": 400, "message": f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Check if a keycard already exists for this booking
        existing_keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=data["booking_id"]))
        if existing_keycard:
            print(f"Keycard already exists for booking {data['booking_id']}")  # Add detailed logging
            return jsonify({"code": 400, "message": "Keycard already exists for this booking."}), 400

        # Get the booking information
        booking_url = f"http://booking:5002/bookings/{data['booking_id']}"
        print("Fetching booking from:", booking_url)  # Add logging
        booking_response = requests.get(booking_url)
        print("Booking response:", booking_response.text)  # Add logging

        if booking_response.status_code != 200:
            return jsonify({"code": 400, "message": f"Invalid booking ID. Booking service returned: {booking_response.text}"}), 400

        booking_data = booking_response.json()["data"]
        check_in_date = booking_data["check_in"]  # Format: YYYY-MM-DD
        check_out_date = booking_data["check_out"]  # Format: YYYY-MM-DD

        # Convert to datetime objects
        check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
        check_out = datetime.strptime(check_out_date, "%Y-%m-%d")

        # Get today's date
        today = datetime.utcnow().date()

        # If check-in has not occurred, do not generate keycard
        # Bypass this check for testing in development environment
        if environ.get('FLASK_ENV') != 'development' and today < check_in:
            print(f"Check-in date validation: today={today}, check_in={check_in}")  # Add detailed logging
            return jsonify({"code": 400, "message": "Guest has not checked in yet."}), 400

        # convert to `expires_at` (Check-Out Date at 3 PM)
        expires_at = check_out + timedelta(hours=15)  # 3 PM on check-out date

        # Create a new keycard for the guest
        try:
            new_keycard = Keycard(
                keycard_id=None,  # Let the database auto-generate this
                booking_id=data["booking_id"],
                guest_id=data["guest_id"],
                room_id=data["room_id"],
                key_pin=random.randint(0, 999999),  # Generate integer PIN
                floor=data["floor"],
                issued_at=datetime.utcnow(),
                expires_at=expires_at
            )
            print("Created keycard:", new_keycard.json())  # Add logging
        except Exception as e:
            print("Error creating keycard:", str(e))  # Add logging
            return jsonify({"code": 500, "message": f"Error creating keycard: {str(e)}"}), 500

        try:
            db.session.add(new_keycard)
            db.session.commit()
            print("Keycard saved to database")  # Add logging
            return jsonify({"code": 201, "data": new_keycard.json()}), 201
        except Exception as e:
            print("Error saving keycard:", str(e))  # Add logging
            db.session.rollback()
            return jsonify({"code": 500, "message": f"Error saving keycard: {str(e)}"}), 500
    except Exception as e:
        print("Unexpected error:", str(e))  # Add logging
        return jsonify({"code": 500, "message": f"Unexpected error: {str(e)}"}), 500

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
    keycard.expires_at = None

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