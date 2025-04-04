from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Service URLs from environment variables
GUEST_URL = environ.get("GUEST_URL", "http://guest:5011")
PRICE_URL = environ.get("PRICE_URL", "http://price:8000")

db = SQLAlchemy(app)

class Booking(db.Model):
    __tablename__ = "booking"

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    guest_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.String(36), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    room_type = db.Column(db.String(36), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def json(self):
        return {
            "booking_id": self.booking_id,
            "guest_id": self.guest_id,
            "room_id": self.room_id,
            "check_in": str(self.check_in),
            "check_out": str(self.check_out),
            "room_type": self.room_type,
            "price": self.price
        }

# Only create tables when running in production mode
if not app.config.get("TESTING"):
    with app.app_context():
        db.create_all()

#health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

#create booking
@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()

    check_in = datetime.strptime(data["check_in"], "%Y-%m-%d").date()
    check_out = datetime.strptime(data["check_out"], "%Y-%m-%d").date()

    if check_out <= check_in:
        return jsonify({"code": 400, "message": "Check-out must be after check-in."}), 400

    conflict = db.session.scalars(
        db.select(Booking).filter(
            Booking.room_id == data["room_id"],
            Booking.check_out > check_in,
            Booking.check_in < check_out
        )
    )
    if conflict:
        return jsonify({"code": 400, "message": "Room is already booked for selected period."}), 400

    guest_check = requests.get(f"{GUEST_URL}/guests/{data['guest_id']}")
    if guest_check.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid guest_id."}), 400

    # Fetch price from price microservice
    price_response = requests.get(f"{PRICE_URL}/prices/{data['room_type']}")
    if price_response.status_code != 200:
        return jsonify({"code": 400, "message": "No pricing data for this room type."}), 400
    price_data = price_response.json()
    price = price_data["price"]

    new_booking = Booking(
        
        guest_id=data["guest_id"],
        room_id=data["room_id"],
        check_in=check_in,
        check_out=check_out,
        room_type=data["room_type"],
        price=data["price"]
    )

    try:
        db.session.add(new_booking)
        db.session.commit()
        db.session.refresh(new_booking)
        return jsonify({"code": 201, "data": new_booking.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating booking: {str(e)}"}), 500

#get all bookings
@app.route("/bookings", methods=["GET"])
def get_all_bookings():
    bookings = db.session.scalars(db.select(Booking)).all()
    if bookings:
        return jsonify({"code": 200, "data": {"bookings": [b.json() for b in bookings]}}), 200
    return jsonify({"code": 404, "message": "No bookings found."}), 404

#get booking by id
@app.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))
    if booking:
        return jsonify({"code": 200, "data": booking.json()}), 200
    return jsonify({"code": 404, "message": "Booking not found."}), 404

#update booking (doesnt work -- always returns room already booked for selected dates)
@app.route("/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    data = request.get_json()
    new_check_in = datetime.strptime(data.get("check_in", str(booking.check_in)), "%Y-%m-%d").date()
    new_check_out = datetime.strptime(data.get("check_out", str(booking.check_out)), "%Y-%m-%d").date()
    new_room_id = data.get("room_id", booking.room_id)

    if new_check_out <= new_check_in:
        return jsonify({"code": 400, "message": "Check-out must be after check-in."}), 400

    conflict = db.session.scalars(
        db.select(Booking).filter(
            Booking.booking_id != booking_id,
            Booking.check_out > new_check_in,
            Booking.check_in < new_check_out
        )
    )
    if conflict:
        return jsonify({"code": 400, "message": "Room is already booked for selected dates."}), 400

    booking.room_id = new_room_id
    booking.check_in = new_check_in
    booking.check_out = new_check_out
    booking.room_type = data.get("room_type", booking.room_type)
    booking.price = data.get("price", booking.price)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": booking.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating booking: {str(e)}"}), 500

#cancel booking (if update booking is not needed, then u can js remove this too)
@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
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
        return jsonify({"code": 500, "message": f"Error deleting booking: {str(e)}"}), 500

#get active booking (doesnt work too)
@app.route("/bookings/active/<string:room_id>", methods=["GET"])
def get_active_booking(room_id):
    today = datetime.utcnow().date()
    active_booking = db.session.scalars(
        db.select(Booking).filter(
            Booking.room_id == room_id,
            Booking.check_in <= today,
            Booking.check_out >= today
        )
    )

    if active_booking:
        return jsonify({"code": 200, "data": active_booking.json()}), 200
    return jsonify({"code": 404, "message": "No active booking found."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
