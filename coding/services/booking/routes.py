from flask import Blueprint, request, jsonify
from booking.models import Booking
from booking.database import db
import requests
from datetime import datetime

booking_bp = Blueprint("booking_bp", __name__)

@booking_bp.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()
    
    try:
        # Validate staff (user)
        staff_res = requests.get(f"http://localhost:5001/users/{data['user_id']}")
        if staff_res.status_code != 200:
            return jsonify({"code": 404, "message": "Invalid staff ID"}), 404

        # Validate customer
        cust_res = requests.get(f"http://localhost:5003/customers/{data['customer_id']}")
        if cust_res.status_code != 200:
            return jsonify({"code": 404, "message": "Invalid customer ID"}), 404

        # Check if room is booked during the given dates
        overlapping = Booking.query.filter(
            Booking.room_id == data["room_id"],
            Booking.status != "CANCELLED",
            Booking.check_in_date <= datetime.strptime(data["check_out_date"], "%Y-%m-%d"),
            Booking.check_out_date >= datetime.strptime(data["check_in_date"], "%Y-%m-%d")
        ).first()

        if overlapping:
            return jsonify({"code": 409, "message": "Room is already booked during this period."}), 409

        new_booking = Booking(
            user_id=data["user_id"],
            customer_id=data["customer_id"],
            room_id=data["room_id"],
            check_in_date=data["check_in_date"],
            check_out_date=data["check_out_date"]
        )

        db.session.add(new_booking)
        db.session.commit()

        notification_payload = {
            "user_id": data["customer_id"],  # assuming customer is the user
            "type": "email",
            "title": "Booking Confirmed",
            "message": f"Your booking for room {data['room_id']} is confirmed from {data['check_in_date']} to {data['check_out_date']}.",
            "metadata": {"booking_id": new_booking.booking_id}
        }

        try:
            notif_res = requests.post("http://localhost:8005/notifications", json=notification_payload)
            if notif_res.status_code >= 400:
                print("Notification failed:", notif_res.json())
        except Exception as e:
            print("Error contacting notification service:", str(e))

        return jsonify({"code": 201, "data": new_booking.json()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Failed to create booking: {str(e)}"}), 500


@booking_bp.route("/bookings", methods=["GET"])
def get_all_bookings():
    bookings = Booking.query.all()
    if bookings:
        return jsonify({"code": 200, "data": [b.json() for b in bookings]}), 200
    return jsonify({"code": 404, "message": "No bookings found."}), 404


@booking_bp.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        return jsonify({"code": 200, "data": booking.json()}), 200
    return jsonify({"code": 404, "message": "Booking not found."}), 404


@booking_bp.route("/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    data = request.get_json()
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    for key in ["room_id", "check_in_date", "check_out_date", "status"]:
        if key in data:
            setattr(booking, key, data[key])

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": booking.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating booking: {str(e)}"}), 500


@booking_bp.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
def cancel_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"code": 404, "message": "Booking not found."}), 404

    booking.status = "CANCELLED"
    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Booking cancelled."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error cancelling booking: {str(e)}"}), 500
