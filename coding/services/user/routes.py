from flask import Blueprint, request, jsonify
from user.models import User
from user.database import db
from werkzeug.security import generate_password_hash, check_password_hash

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/users", methods=["POST"])
def register_user():
    data = request.get_json()

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"code": 400, "message": "Email already registered"}), 400

    new_user = User(
        name=data["name"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        role=data["role"]
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"code": 201, "data": new_user.json()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "message": f"Error creating user: {str(e)}"}), 500

@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"code": 404, "message": "User not found"}), 404
    return jsonify({"code": 200, "data": user.json()}), 200

@user_bp.route("/users/authenticate", methods=["POST"])
def authenticate_user():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user or not check_password_hash(user.password_hash, data["password"]):
        return jsonify({"code": 401, "message": "Invalid email or password"}), 401

    return jsonify({"code": 200, "data": user.json()}), 200
