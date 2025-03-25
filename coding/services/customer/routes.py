# customer/routes.py
from flask import Blueprint, request, jsonify
from customer.models import Customer
from customer.database import db
from datetime import datetime

customer_bp = Blueprint('customer_bp', __name__)

# Create Customer Endpoint
@customer_bp.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()

    # Check if email already exists
    if Customer.query.filter_by(email=data["email"]).first():
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
        return jsonify({"code": 201, "data": new_customer.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating customer: {str(e)}"}), 500


# Get All Customers Endpoint
@customer_bp.route("/customers", methods=["GET"])
def get_all_customers():
    customers = Customer.query.all()
    if customers:
        return jsonify({"code": 200, "data": {"customers": [c.json() for c in customers]}}), 200
    return jsonify({"code": 404, "message": "No customers found."}), 404


# Get Single Customer Endpoint
@customer_bp.route("/customers/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        return jsonify({"code": 200, "data": customer.json()}), 200
    return jsonify({"code": 404, "message": "Customer not found."}), 404

# Update Customer Endpoint
@customer_bp.route("/customers/<int:customer_id>/update", methods=["PUT"])
def update_customer(customer_id):
    data = request.get_json()
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    # Check if any of the fields have changed; if so, reset verification status
    fields_to_check = ["name", "address", "contact", "email", "nationality"]
    verification_reset = any(data.get(field) and data[field] != getattr(customer, field) for field in fields_to_check)

    customer.name = data.get("name", customer.name)
    customer.address = data.get("address", customer.address)
    customer.contact = data.get("contact", customer.contact)
    customer.email = data.get("email", customer.email)
    customer.nationality = data.get("nationality", customer.nationality)

    if verification_reset:
        customer.verified = False

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": customer.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error updating customer: {str(e)}"}), 500


# Verify Customer Endpoint
@customer_bp.route("/customers/<int:customer_id>/verify", methods=["PUT"])
def verify_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({"code": 404, "message": "Customer not found."}), 404

    customer.verified = True
    try:
        db.session.commit()
        return jsonify({"code": 200, "message": "Customer verified successfully.", "data": customer.json()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error verifying customer: {str(e)}"}), 500
