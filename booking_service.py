from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/booking"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)


# Booking Model
class Booking(db.Model):
    __tablename__ = "booking"

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Staff who created the booking
    customer_id = db.Column(db.Integer, nullable=False)  # The actual customer staying
    room_id = db.Column(db.String(36), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("CONFIRMED", "CANCELLED", "CHECKED-IN", "CHECKED-OUT"), default="CONFIRMED")

    def json(self):
        return {
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "room_id": self.room_id,
            "check_in_date": str(self.check_in_date),
            "check_out_date": str(self.check_out_date),
            "status": self.status
        }


# Auto-create table if it doesn't exist
with app.app_context():
    db.create_all()


# create a Booking
@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()

    # validate check-in and check-out dates
    check_in = datetime.strptime(data["check_in_date"], "%Y-%m-%d").date()
    check_out = datetime.strptime(data["check_out_date"], "%Y-%m-%d").date()

    if check_out <= check_in:
        return jsonify({"code": 400, "message": "Check-out date must be later than check-in date."}), 400

    # check if room is available (ignore cancelled bookings)
    conflicting_booking = db.session.scalars(
        db.select(Booking).filter(
            Booking.room_id == data["room_id"],
            Booking.status != "CANCELLED",
            Booking.check_out_date > check_in,
            Booking.check_in_date < check_out
        )
    ).first()

    if conflicting_booking:
        return jsonify({"code": 400, "message": "Room is already booked for the selected period."}), 400

    # verify user_id (staff) using user_management API
    user_check_url = f"http://localhost:5001/users/{data['user_id']}/exists"
    user_response = requests.get(user_check_url)

    if user_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid staff user_id. Staff does not exist."}), 400

    # verify customer_id using customer_management API

    customer_check_url = f"http://localhost:5003/customers/{data['customer_id']}"
    customer_response = requests.get(customer_check_url)

    if customer_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid customer_id. Customer does not exist."}), 400

    # create the booking
    new_booking = Booking(
        user_id=data["user_id"],
        customer_id=data["customer_id"],
        room_id=data["room_id"],
        check_in_date=check_in,
        check_out_date=check_out
    )

    try:
        db.session.add(new_booking)
        db.session.commit()
        db.session.refresh(new_booking)
        return jsonify({"code": 201, "data": new_booking.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating booking: {str(e)}"}), 500


@app.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))

    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    return jsonify({"code": 200, "data": booking.json()}), 200

# get all bookings
@app.route("/bookings", methods=["GET"])
def get_all_bookings():
    bookinglist = db.session.scalars(db.select(Booking)).all()
    return jsonify({"code": 200, "data": {"bookings": [b.json() for b in bookinglist]}}) if bookinglist else jsonify({"code": 404, "message": "No bookings found."}), 404


# update booking (Switch Room or Dates)
@app.route("/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    data = request.get_json()
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))

    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    new_room_id = data.get("room_id", booking.room_id)
    new_check_in = data.get("check_in_date", booking.check_in_date)
    new_check_out = data.get("check_out_date", booking.check_out_date)

    if isinstance(new_check_in, str):
        new_check_in = datetime.strptime(new_check_in, "%Y-%m-%d").date()
    if isinstance(new_check_out, str):
        new_check_out = datetime.strptime(new_check_out, "%Y-%m-%d").date()

    if new_check_out <= new_check_in:
        return jsonify({"code": 400, "message": "Check-out date must be later than check-in date."}), 400

    conflicting_booking = db.session.scalars(
        db.select(Booking).filter(
            Booking.room_id == new_room_id,
            Booking.booking_id != booking_id,
            Booking.status != "CANCELLED",
            Booking.check_out_date > new_check_in,
            Booking.check_in_date < new_check_out
        )
    ).first()

    if conflicting_booking:
        return jsonify({"code": 400, "message": "Room is already booked for the selected period."}), 400

    booking.room_id = new_room_id
    booking.check_in_date = new_check_in
    booking.check_out_date = new_check_out

    if "status" in data:
        if data["status"] not in ["CONFIRMED", "CANCELLED", "CHECKED-IN", "CHECKED-OUT"]:
            return jsonify({"code": 400, "message": "Invalid status update."}), 400
        booking.status = data["status"]

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": booking.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating booking: {str(e)}"}), 500


#cancel booking 
@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
def cancel_booking(booking_id):
    booking = db.session.scalar(db.select(Booking).filter_by(booking_id=booking_id))

    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    booking.status = "CANCELLED"

    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Booking cancelled. Room is now available for new bookings."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error cancelling booking: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
