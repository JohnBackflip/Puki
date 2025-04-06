from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)

CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Promotion(db.Model):
    __tablename__ = "promotion"
    
    promo_id = db.Column(db.Integer, primary_key=True)
    promo_name = db.Column(db.String(100), nullable=False)
    promo_code = db.Column(db.String(50), nullable=False, unique=True)
    promo_start = db.Column(db.Date, nullable=False)
    promo_end = db.Column(db.Date, nullable=False)
    promo_discount = db.Column(db.Float, nullable=False)
    room_type = db.Column(db.Enum("Single", "Family", "PresidentialSuite"), nullable=False)
    
    def json(self):
        return {
            "promo_id": self.promo_id,
            "promo_name": self.promo_name,
            "promo_code": self.promo_code,
            "promo_start": str(self.promo_start),
            "promo_end": str(self.promo_end),
            "promo_discount": self.promo_discount,
            "room_type": self.room_type
        }

# Create a new promotion
@app.route("/promotion", methods=["POST"])
def add_promotion():
    data = request.get_json()
    
    promo_name = data.get("promo-name")
    promo_code = data.get("promo-code")
    promo_start = datetime.strptime(data.get("promo-start"), "%Y-%m-%d")
    promo_end = datetime.strptime(data.get("promo-end"), "%Y-%m-%d")
    promo_discount = data.get("promo-discount")
    room_type = data.get("room-type")
    
    # Validate required fields
    if not all([promo_name, promo_code, promo_start, promo_end, promo_discount, room_type]):
        return jsonify({"code": 400, "message": "All fields are required."}), 400
    
    # Check if the promotion code already exists
    if db.session.query(Promotion).filter_by(promo_code=promo_code).first():
        return jsonify({"code": 400, "message": "Promotion code already exists."}), 400

    # Create new promotion entry
    new_promotion = Promotion(
        promo_name=promo_name,
        promo_code=promo_code,
        promo_start=promo_start,
        promo_end=promo_end,
        promo_discount=promo_discount,
        room_type=room_type
    )
    
    try:
        db.session.add(new_promotion)
        db.session.commit()
        return jsonify({"code": 201, "message": "Promotion added successfully.", "data": new_promotion.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error adding promotion: {str(e)}"}), 500

# Get all current promotions
@app.route("/promotion/all", methods=["GET"])
def get_promotions():
    promotions = Promotion.query.all()
    return jsonify({
        "code": 200,
        "data": {"promotions": [promotion.json() for promotion in promotions]}
    }), 200

# Get applicable promotion
@app.route("/promotion/applicable", methods=["GET"])
def get_applicable_promotion():
    room_type = request.args.get("room_type", "").lower()
    date = request.args.get("date")

    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    except:
        return jsonify({"code": 400, "message": "Invalid date format. Use YYYY-MM-DD."}), 400

    promotions = Promotion.query.all()
    for promo in promotions:
        if (
            promo.room_type.lower() in [room_type, "all"]
            and promo.promo_start <= date_obj <= promo.promo_end
        ):
            return jsonify({"code": 200, "data": promo.json()}), 200

    return jsonify({"code": 404, "message": "No applicable promotion found."}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5015, debug=True)
