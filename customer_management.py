from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/customer"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)

# Customer Model
class Customer(db.Model):
    __tablename__ = "customer"

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    passport_nric = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    nationality = db.Column(db.String(64), nullable=False)

    def json(self):
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "passport_nric": self.passport_nric,
            "address": self.address,
            "contact": self.contact,
            "email": self.email,
            "nationality": self.nationality
        }


# Auto-create table if it doesn't exist
with app.app_context():
    db.create_all()


#create customers
@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()

    # Check if passport/NRIC or email already exists
    if db.session.scalar(db.select(Customer).filter_by(passport_nric=data["passport_nric"])):
        return jsonify({"code": 400, "message": "A customer with this passport/NRIC already exists."}), 400

    if db.session.scalar(db.select(Customer).filter_by(email=data["email"])):
        return jsonify({"code": 400, "message": "A customer with this email already exists."}), 400

    new_customer = Customer(
        name=data["name"],
        passport_nric=data["passport_nric"],
        address=data["address"],
        contact=data["contact"],
        email=data["email"],
        nationality=data["nationality"]
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
    return jsonify({"code": 200, "data": {"customers": [c.json() for c in customer_list]}}) if customer_list else jsonify({"code": 404, "message": "No customers found."}), 404


# get specific customer by ID
@app.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))
    return jsonify({"code": 200, "data": customer.json()}) if customer else jsonify({"code": 404, "message": "Customer not found."}), 404


# update customer details
@app.route("/customers/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json()
    customer = db.session.scalar(db.select(Customer).filter_by(customer_id=customer_id))

    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    # Update only the provided fields
    customer.name = data.get("name", customer.name)
    customer.passport_nric = data.get("passport_nric", customer.passport_nric)
    customer.address = data.get("address", customer.address)
    customer.contact = data.get("contact", customer.contact)
    customer.email = data.get("email", customer.email)
    customer.nationality = data.get("nationality", customer.nationality)

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": customer.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating customer: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
