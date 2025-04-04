#integrate with booking service

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

# Define the Price model
class Price(db.Model):
    __tablename__ = "price"

    room_id = db.Column(db.String(36), primary_key=True)
    room_type = db.Column(db.String(50), nullable=False, unique=True)
    price = db.Column(db.Float, nullable=False)

    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "price": self.price,
        }

#create table
with app.app_context():
    db.create_all()

#health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Get all prices
@app.get("/prices/")
def get_all_prices():
    prices = Price.query.all()
    return jsonify([{"room_type": price.room_type, "price": price.price} for price in prices])

# Get price by room type
@app.get("/prices/<room_type>")
def get_price_by_room_type(room_type: str):
    price = Price.query.filter_by(room_type=room_type).first()
    if not price:
        return jsonify({"error": "Price not found"}), 404
    return jsonify({"room_type": price.room_type, "price": price.price})

# Create a new price
@app.post("/prices/")
def create_price():
    data = request.get_json()
    room_type = data.get('room_type')
    price = data.get('price')

    if not room_type or not price:
        return jsonify({"error": "Missing required fields"}), 400

    new_price = Price(room_type=room_type, price=price)
    db.session.add(new_price)
    db.session.commit()
    return jsonify({"room_type": new_price.room_type, "price": new_price.price}), 201

# Update an existing price
@app.put("/prices/<room_type>")
def update_price(room_type: str):
    data = request.get_json()
    new_price_value = data.get('price')

    price = Price.query.filter_by(room_type=room_type).first()
    if not price:
        return jsonify({"error": "Price not found"}), 404

    price.price = new_price_value
    db.session.commit()
    return jsonify({"room_type": price.room_type, "price": price.price})

@app.route("/prices/events", methods=["POST"])
def adjust_prices_by_season():
    data = request.get_json()
    season = data.get("season", "").strip().lower()

    # Define festive multipliers
    seasonal_multipliers = {
        "christmas": 1.25,
        "new year": 1.20,
        "national day": 1.15,
        "off-peak": 0.90
    }

    multiplier = seasonal_multipliers.get(season, 1.0)

    prices = Price.query.all()
    updated_prices = []

    for p in prices:
        original = p.price
        new_price = round(original * multiplier, 2)
        p.price = new_price
        updated_prices.append({"room_type": p.room_type, "old": original, "new": new_price})

    try:
        db.session.commit()
        return jsonify({"season": season, "updated": updated_prices}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8006, debug=True)
