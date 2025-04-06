from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime

app = Flask(__name__)
CORS(app)

app.json.sort_keys = False 

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Booking Model
class Booking(db.Model):
    __tablename__ = "booking"

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guest_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.String(36), nullable=True)
    floor = db.Column(db.Integer, nullable=True)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    room_type = db.Column(db.String(36), nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    def json(self):
        return {
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "room_id": self.room_id,
            "floor": self.floor,
            "check_in": str(self.check_in),
            "check_out": str(self.check_out),
            "room_type": self.room_type,
            "price": self.price
        }


# Auto-create table if it doesn't exist
with app.app_context():
    db.create_all()

#health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

#get all bookings
@app.route("/booking", methods=["GET"])
def get_all_bookings():
    bookings = db.session.scalars(db.select(Booking)).all()
    if bookings:
        return jsonify({"code": 200, "data": {"bookings": [b.json() for b in bookings]}}), 200
    return jsonify({"code": 404, "message": "No bookings found."}), 404

#get booking by id
@app.route("/booking/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))
    if booking:
        return jsonify({"code": 200, "data": booking.json()}), 200
    return jsonify({"code": 404, "message": "Booking not found."}), 404

#update booking
@app.route("/booking/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    data = request.get_json()

    new_check_in = datetime.strptime(data.get("check_in", str(booking.check_in)), "%Y-%m-%d").date()
    new_check_out = datetime.strptime(data.get("check_out", str(booking.check_out)), "%Y-%m-%d").date()

    if new_check_out <= new_check_in:
        return jsonify({"code": 400, "message": "Check-out must be after check-in."}), 400

    # Only check for conflicts in the same room
    conflict_query = db.select(Booking).filter(
        Booking.booking_id != booking_id,
        Booking.check_out > new_check_in,
        Booking.check_in < new_check_out
    )

    conflicts = db.session.scalars(conflict_query).all()

    # Debug logging
    print(f"Checking conflicts for Booking ID {booking_id}")
    print(f"New Check-in: {new_check_in}, Check-out: {new_check_out}")
    print(f"Conflicts found: {len(conflicts)}")
    for c in conflicts:
        print(f" - Conflict Booking ID {c.booking_id}, Room {c.room_id}, {c.check_in} → {c.check_out}")

    if conflicts:
        return jsonify({"code": 400, "message": "Room is already booked for selected dates."}), 400

    # Apply changes
    booking.check_in = new_check_in
    booking.check_out = new_check_out

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": booking.json()}), 200
    except Exception as e:
        db.session.rollback()
        print("Error updating booking:", str(e))
        return jsonify({"code": 500, "message": "Error updating booking:"}), 500

#postman
# {    
#     "check_in": "2025-05-25",    
#     "check_out": "2025-05-28"                              
# }

#cancel booking
@app.route("/booking/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    try:
        db.session.delete(booking)
        db.session.commit()
        return jsonify({"code": 200, "message": "Booking cancelled and deleted."}), 200
    except Exception as e:
        db.session.rollback()
        print("Error deleting booking:", str(e))
        return jsonify({"code": 500, "message": "Error deleting booking."}), 500

#get active bookings
@app.route("/booking/active", methods=["GET"])
def get_active_booking():
    today = datetime.utcnow().date()
    active_bookings = db.session.scalars(
        db.select(Booking).filter(
            Booking.check_in <= today,
            Booking.check_out >= today
        )
    ).all()

    if active_bookings:
        return jsonify({
            "code": 200,
            "data": {
                "active_bookings": [b.json() for b in active_bookings]
            }
        }), 200
    return jsonify({"code": 404, "message": "No active booking found."}), 404

# Check if a room is available for a given date range
@app.route("/booking/availability", methods=["POST"])
def check_availability():
    data = request.get_json()
    room_id = data["room_id"]
    check_in = datetime.strptime(data["check_in"], "%Y-%m-%d").date()
    check_out = datetime.strptime(data["check_out"], "%Y-%m-%d").date()
    
    # Optionally exclude a specific booking (for updates)
    exclude_booking_id = data.get("exclude_booking_id")
    
    query = db.select(Booking).filter(
        Booking.room_id == room_id,
        Booking.check_out > check_in,
        Booking.check_in < check_out
    )
    
    if exclude_booking_id:
        query = query.filter(Booking.booking_id != exclude_booking_id)
        
    conflicting_booking = db.session.scalar(query)
    
    if conflicting_booking:
        return jsonify({"code": 400, "available": False, "message": "Room is not available for the selected period."}), 400
    
    return jsonify({"code": 200, "available": True, "message": "Room is available for the selected period."}), 200

# Create a booking
@app.route("/booking", methods=["POST"])
def create_booking():
    data = request.get_json()
    guest_id = data.get("guest_id")
    room_id = data.get("room_id")
    floor = data.get("floor")
    check_in = datetime.strptime(data.get("check_in"), "%Y-%m-%d").date()
    check_out = datetime.strptime(data.get("check_out"), "%Y-%m-%d").date()
    room_type = data.get("room_type")
    price = data.get("price")
    
    if not all([guest_id, check_in, check_out, room_type, price]):
        return jsonify({"code": 400, "message": "Missing required fields."}), 400
    
    if check_out <= check_in:
        return jsonify({"code": 400, "message": "Check-out must be after check-in."}), 400
    
    # Check if the room is available for the given dates
    conflict = None
    if room_id:
        conflict = db.session.scalar(
            db.select(Booking).filter(
                Booking.room_id == room_id,
                Booking.check_out > check_in,
                Booking.check_in < check_out
            )
        )
    
    if conflict:
        return jsonify({"code": 400, "message": "Room is already booked for the selected period."}), 400
    
    new_booking = Booking(
        guest_id=guest_id,
        room_id=room_id,
        floor=floor,
        check_in=check_in,
        check_out=check_out,
        room_type=room_type,
        price=price
    )
    
    try:
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({"code": 201, "data": new_booking.json()}), 201
    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"code": 500, "message": "Error creating booking."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)