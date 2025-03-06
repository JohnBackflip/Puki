from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

# Configure MySQL database
app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/user"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)

# User Model (Admin & Staff)
class User(db.Model):
    __tablename__ = "user"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)    
    name = db.Column(db.String(64), nullable=False) 
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)  # Hashed Password
    role = db.Column(db.String(10), nullable=False)  # "admin" or "staff"

    def json(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }

# Create a new user (Admin Only)
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()

    # Check if email already exists
    if db.session.scalar(db.select(User).filter_by(email=data["email"])):
        return jsonify({"code": 400, "message": "User already exists."}), 400

    # Validate role
    if data["role"] not in ["admin", "staff"]:
        return jsonify({"code": 400, "message": "Invalid role. Choose 'admin' or 'staff'."}), 400


    new_user = User(
        name=data["name"],
        email=data["email"],
        password_hash=data["password"],
        role=data["role"],
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)  # Forces Flask to fetch the correct ID
        return jsonify({"code": 201, "data": new_user.json()}), 201
    except Exception as e:
        db.session.rollback()  # Ensures no skipped IDs
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500
    

# Get all users (Admin Only)
@app.route("/users", methods=["GET"])
def get_all_users():
    userlist = db.session.scalars(db.select(User)).all()
    if userlist:
        return jsonify({"code": 200, "data": {"users": [user.json() for user in userlist]}})
    return jsonify({"code": 404, "message": "No users found."}), 404

# Get a specific user by ID
@app.route("/users/<string:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.scalar(db.select(User).filter_by(user_id=user_id))
    if user:
        return jsonify({"code": 200, "data": user.json()})
    return jsonify({"code": 404, "message": "User not found."}), 404

# Update user details (Admin Only)
@app.route("/users/<string:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    user = db.session.scalar(db.select(User).filter_by(user_id=user_id))

    if not user:
        return jsonify({"code": 404, "message": "User not found."}), 404

    if "name" in data:
        user.name = data["name"]
    if "role" in data and data["role"] in ["admin", "staff"]:
        user.role = data["role"]

    try:
        db.session.commit()
        return jsonify({"code": 200, "data": user.json()}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500

# Delete a user (Admin Only)
@app.route("/users/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.scalar(db.select(User).filter_by(user_id=user_id))

    if not user:
        return jsonify({"code": 404, "message": "User not found."}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"code": 200, "message": "User deleted successfully."}), 200
    except Exception as e:
        return jsonify({"code": 500, "message": f"An error occurred: {str(e)}"}), 500

# Check if user exists by email
@app.route("/users/<int:user_id>/exists", methods=["GET"])
def check_user_exists(user_id):
    user = db.session.scalar(db.select(User).filter_by(user_id=user_id))
    if user:
        return jsonify({"code": 200, "message": "User exists."}), 200
    return jsonify({"code": 404, "message": "User not found."}), 404


# User Login
@app.route("/users/login", methods=["POST"])
def login_user():
    data = request.get_json()
    user = db.session.scalar(db.select(User).filter_by(email=data["email"]))

    if user and user.password_hash == data["password"]:
        return jsonify({"code": 200, "data": user.json()}), 200
    return jsonify({"code": 401, "message": "Invalid email or password."}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
