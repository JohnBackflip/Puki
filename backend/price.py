#integrate with booking service

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///price.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Define the Price model
class Price(db.Model):
    __tablename__ = "price"

    room_id = db.Column(db.String(36), primary_key=True)
    floor = db.Column(db.Integer, nullable=False)
    room_type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, room_id, floor, room_type, price):
        self.room_id = room_id  # Use the provided room_id
        self.floor = floor
        self.room_type = room_type
        self.price = price

    def json(self):
        return {
            "room_id": self.room_id,
            "floor": self.floor,
            "room_type": self.room_type,
            "price": self.price,
        }
    
#create table
with app.app_context():
    db.create_all()
    
    # Add price for room 103 if it doesn't exist
    existing_price = db.session.query(Price).filter_by(room_id="103").first()
    if not existing_price:
        print("Creating price for room 103")
        new_price = Price(
            room_id="103",
            floor=1,
            room_type="PresidentialSuite",
            price=500.0
        )
        db.session.add(new_price)
        try:
            db.session.commit()
            print("Created price for room 103")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating price for room 103: {str(e)}")

#health check
@app.route("/health")
def health():
    return {"status": "healthy"}

# Get all prices
@app.route("/price", methods=["GET"])
def get_all_prices():
    prices = Price.query.all()
    return jsonify([price.json() for price in prices])

# Get prices by room type
@app.route("/price/<room_type>", methods=["GET"])
def get_price_by_room_type(room_type: str):
    prices = Price.query.filter_by(room_type=room_type).all()
    if not prices:
        return jsonify({"error": "Price not found"}), 404
    return jsonify([{"room_type": price.room_type, "price": price.price} for price in prices])

#create a price
@app.route("/prices/<room_id>", methods=["POST"])
def create_price(room_id: str):
    data = request.get_json()
    room_type = data.get('room_type')
    price = data.get('price')
    floor = data.get('floor')  # Add floor as a required field

    # Check if required fields are provided
    if not all([room_type, price, floor]):
        return jsonify({"error": "Missing required fields: 'room_type', 'price', 'floor'"}), 400

    # Check if the price entry with the same room_id already exists
    existing_price = db.session.query(Price).filter_by(room_id=room_id).first()
    if existing_price:
        return jsonify({"error": f"Price entry for room_id {room_id} already exists."}), 400

    # Create new price with floor
    new_price = Price(room_id=room_id, floor=floor, room_type=room_type, price=price)
    db.session.add(new_price)

    try:
        db.session.commit()
        return jsonify({"room_id": new_price.room_id, "room_type": new_price.room_type, "price": new_price.price}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": f"Failed to insert price for room_id {room_id}."}), 500
    
# Update an existing price by room_type
@app.route("/price/<room_type>", methods=["PUT"])
def update_price(room_type: str):
    data = request.get_json()
    new_price_value = data.get('price')

    prices = Price.query.filter_by(room_type=room_type).all()
    if not prices:
        return jsonify({"error": "Price not found"}), 404
    
    # Update price for all matching room_types
    for price in prices:
        price.price = new_price_value
        
    db.session.commit()
    return jsonify({"room_type": price.room_type, "price": price.price})

# Update price by room_id
@app.route("/price/<int:room_id>", methods=["PUT"])
def update_price_by_room_id(room_id: int):
    data = request.get_json()
    new_price_value = data.get('price')

    # Fetch the price by room_id
    price = Price.query.filter_by(room_id=room_id).first()

    if not price:
        return jsonify({"error": "Room ID not found"}), 404

    # Update the price for the given room_id
    price.price = new_price_value

    db.session.commit()
    return jsonify({"room_id": price.room_id, "room_type": price.room_type, "new_price": price.price})

# Adjust prices by season
@app.route("/price/events", methods=["POST"])
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

# Get price by room_id
@app.route("/price/<string:room_id>", methods=["GET"])
def get_price_by_room_id(room_id: str):
    print(f"Looking for price with room_id: '{room_id}'")
    
    price = db.session.query(Price).filter_by(room_id=room_id).first()
    if price:
        print("Match found!")
        return jsonify(price.json())
    
    print("No match found")
    return jsonify({"error": "Price not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
