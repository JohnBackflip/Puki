import random
import requests
from datetime import datetime,timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
CORS(app)


app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)


#keycard model
class Keycard(db.Model):
    __tablename__ = "keycard"

    keycard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, nullable=False, unique=True)  # Links to a booking
    user_id = db.Column(db.Integer, nullable=True)  # Staff who issued the key (None for self check-in)
    customer_id = db.Column(db.Integer, nullable=False)  # Customer using the key
    room_id = db.Column(db.String(36), nullable=False)
    key_pin = db.Column(db.String(6), nullable=False)  # ✅ 6-digit PIN
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Null if not expired

    def json(self):
        return {
            "keycard_id": self.keycard_id,
            "booking_id": self.booking_id,
            "user_id": self.user_id, 
            "customer_id": self.customer_id,
            "room_id": self.room_id,
            "key_pin": self.key_pin,
            "issued_at": str(self.issued_at),
            "expires_at": str(self.expires_at) if self.expires_at else None
        }


# auto-create table if not ald
with app.app_context():
    db.create_all()


@app.route("/keycards", methods=["POST"])
def generate_keycard():
    data = request.get_json()

    # check if a keycard already exists for this booking
    existing_keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=data["booking_id"]))

    if existing_keycard:
        return jsonify({"code": 400, "message": "Keycard already exists for this booking."}), 400

    #gets check-out date
    booking_url = f"http://localhost:5002/bookings/{data['booking_id']}"
    booking_response = requests.get(booking_url)

    if booking_response.status_code != 200:
        return jsonify({"code": 400, "message": "Invalid booking ID."}), 400

    booking_data = booking_response.json()["data"]
    check_out_date = booking_data["check_out_date"]  # ✅ Format: YYYY-MM-DD

    # convert to `expires_at` (Check-Out Date at 3 PM)
    expires_at = datetime.strptime(check_out_date, "%Y-%m-%d") + timedelta(hours=15)  # 3 PM

    # allow "user_id" to be None if not provided (Self Check-In)
    new_keycard = Keycard(
        booking_id=data["booking_id"],
        user_id=data.get("user_id"),  
        customer_id=data["customer_id"],
        room_id=data["room_id"],
        key_pin=str(random.randint(000000, 999999)).zfill(6),  
        expires_at=expires_at  # ✅ Now automatically set to check-out at 3 PM
    )

    try:
        db.session.add(new_keycard)
        db.session.commit()
        return jsonify({"code": 201, "data": new_keycard.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error generating keycard: {str(e)}"}), 500


# ✅ Get Keycard by Booking ID
@app.route("/keycards/<int:booking_id>", methods=["GET"])
def get_keycard(booking_id):
    keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))
    return jsonify({"code": 200, "data": keycard.json()}) if keycard else jsonify({"code": 404, "message": "Keycard not found."}), 404


# ✅ Renew Keycard (Reissue a New PIN)
@app.route("/keycards/<int:booking_id>/renew", methods=["PUT"])
def renew_keycard(booking_id):
    keycard = db.session.scalar(db.select(Keycard).filter_by(booking_id=booking_id))

    if not keycard:
        return jsonify({"code": 404, "message": "Keycard not found."}), 404

    keycard.key_pin = str(random.randint(000000, 999999)).zfill(6) 
    keycard.issued_at = datetime.utcnow()
    keycard.expires_at = None  # ✅ Reset expiration

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": keycard.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error renewing keycard: {str(e)}"}), 500


# ✅ Expire Keycard (User Checks Out)
@app.route("/keycards/<int:booking_id>/expire", methods=["PUT"])
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
