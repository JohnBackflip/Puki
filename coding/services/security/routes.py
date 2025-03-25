# security/routes.py
from flask import Blueprint, request, jsonify
from security.models import Keycard
from security.database import db
from datetime import datetime, timedelta
import random
import requests

security_bp = Blueprint('security_bp', __name__)

# Generate Keycard Endpoint
@security_bp.route("/keycards", methods=["POST"])
def generate_keycard():
    data = request.get_json()
    
    # Check if a keycard already exists for this booking
    if Keycard.query.filter_by(booking_id=data["booking_id"]).first():
        return jsonify({"code": 400, "message": "Keycard already exists for this booking."}), 400

    # Retrieve booking details from booking service
    booking_url = f"http://localhost:5002/bookings/{data['booking_id']}"
    booking_response = requests.get(booking_url)
    if booking_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.json().get("data")
    check_out_date = booking_data["check_out_date"]
    expires_at = datetime.strptime(check_out_date, "%Y-%m-%d") + timedelta(hours=15)

    new_keycard = Keycard(
        booking_id=data["booking_id"],
        user_id=data.get("user_id"),
        customer_id=data["customer_id"],
        room_id=data["room_id"],
        key_pin=str(random.randint(0, 999999)).zfill(6),
        expires_at=expires_at
    )

    try:
        db.session.add(new_keycard)
        db.session.commit()
        return jsonify({"code": 201, "data": new_keycard.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error generating keycard: {str(e)}"}), 500


# Get Keycard Information Endpoint
@security_bp.route("/keycards/<int:booking_id>", methods=["GET"])
def get_keycard(booking_id):
    keycard = Keycard.query.filter_by(booking_id=booking_id).first()
    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404
    return jsonify({"code": 200, "data": keycard.json()}), 200


# Renew Keycard Endpoint (Generate New PIN)
@security_bp.route("/keycards/<int:booking_id>/renew", methods=["PUT"])
def renew_keycard(booking_id):
    keycard = Keycard.query.filter_by(booking_id=booking_id).first()
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


# Expire Keycard Endpoint (Expire keycard and clear room PIN)
@security_bp.route("/keycards/<int:booking_id>/expire", methods=["PUT"])
def expire_keycard(booking_id):
    keycard = Keycard.query.filter_by(booking_id=booking_id).first()
    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    keycard.expires_at = datetime.utcnow()

    try:
        db.session.commit()
        # Also remove room PIN from room service
        room_update_url = f"http://localhost:5006/rooms/{keycard.room_id}/update-pin"
        room_update_payload = {"room_pin": None}
        try:
            room_response = requests.put(room_update_url, json=room_update_payload)
            if room_response.status_code != 200:
                print("Failed to remove room PIN:", room_response.json())
        except Exception as e:
            print("Error calling room service:", str(e))
        return jsonify({"code": 200, "message": "Keycard expired and room PIN cleared."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error expiring keycard: {str(e)}"}), 500


# Update Keycard Expiry Endpoint
@security_bp.route("/keycards/<int:booking_id>/update-expiry", methods=["PUT"])
def update_keycard_expiry(booking_id):
    data = request.get_json()
    keycard = Keycard.query.filter_by(booking_id=booking_id).first()
    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    try:
        keycard.expires_at = datetime.strptime(data["expires_at"], "%Y-%m-%d %H:%M:%S")
        db.session.commit()
        return jsonify({"code": 200, "data": keycard.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating keycard expiry: {str(e)}"}), 500
