import random
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from datetime import datetime,timedelta


app = Flask(__name__)
CORS(app)
app.json.sort_keys = False 

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)

# Customer Model
class Customer(db.Model):
    __tablename__ = "customer"

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    nationality = db.Column(db.String(64), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)

    def json(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "address": self.address,
            "contact": self.contact,
            "email": self.email,
            "nationality": self.nationality,
            "verified": self.verified,
            "otp": self.otp,
            "otp_expiry": str(self.otp_expiry) if self.otp_expiry else None
        }


# Auto-create table if it doesn't exist
with app.app_context():
    db.create_all()


#create customers
@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()

    # Check if email already exists
    if db.session.scalar(db.select(Customer).filter_by(email=data["email"])):
        return jsonify({"code": 400, "message": "A customer with this email already exists."}), 400

    new_customer = Customer(
        name=data["name"],
        address=data["address"],
        contact=data["contact"],
        email=data["email"],
        nationality=data["nationality"],
        verified=False  # Customers start as unverified
    )

    try:
        db.session.add(new_customer)
        db.session.commit()
        db.session.refresh(new_customer)
        return jsonify({"code": 201, "data": new_customer.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating customer: {str(e)}"}), 500

#get all customers
@app.route("/customers", methods=["GET"])
def get_all_customers():
    customer_list = db.session.scalars(db.select(Customer)).all()

    if customer_list and len(customer_list) > 0: 
        return jsonify({"code": 200, "data": {"customers": [c.json() for c in customer_list]}}), 200
    
    return jsonify({"code": 404, "message": "No customers found."}), 404

# get specific customer by ID
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))
    
    if customer:
        return jsonify({"code": 200, "data": customer.json()}), 200
    
    return jsonify({"code": 404, "message": "Customer not found."}), 404


# update customer details
@app.route("/customers/<int:customer_id>/update", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json()
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))

    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    fields_to_check = ["name", "address","contact", "email", "nationality"]
    verification_reset = any(data.get(field) and data[field] != getattr(customer, field) for field in fields_to_check)

    # Update customer details (if provided)
    customer.name = data.get("name", customer.name)
    customer.address = data.get("address", customer.address)
    customer.contact = data.get("contact", customer.contact)
    customer.email = data.get("email", customer.email)
    customer.nationality = data.get("nationality", customer.nationality)

    if verification_reset:
        customer.verified = False

    # Update OTP for self-check-in
    if "otp" in data and "otp_expiry" in data:
        customer.otp = data["otp"]
        customer.otp_expiry = datetime.strptime(data["otp_expiry"], "%Y-%m-%d %H:%M:%S")

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": customer.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating customer: {str(e)}"}), 500


#verify customer
@app.route("/customers/<int:customer_id>/verify", methods=["PUT"])
def verify_customer(customer_id):
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))

    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    customer.verified = True

    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Customer verified successfully.", "data": customer.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error verifying customer: {str(e)}"}), 500


# Generate & Send a New OTP for Self Check-In
@app.route("/customers/<int:customer_id>/request-otp", methods=["PUT"])
def request_new_otp(customer_id):
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))

    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    # 6 digit otp created
    new_otp = str(random.randint(100000, 999999))
    otp_expiry = datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes

    # db updated w newest otp 
    customer.otp = new_otp
    customer.otp_expiry = otp_expiry

    try:
        db.session.commit()
        # sends otp to api for now
        print(f"New OTP for {customer.email}: {new_otp}")
        return jsonify({"code": 200, "message": "New OTP sent to registered email/phone."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error generating new OTP: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005, debug=True)
