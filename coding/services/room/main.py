from flask import Flask
from flask_cors import CORS
import os
from room.database import db
from room.routes import room_bp
from room.room_management import room_mgmt_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db.init_app(app)

with app.app_context():
    db.create_all()

# Register both blueprints
app.register_blueprint(room_bp)
app.register_blueprint(room_mgmt_bp)

@app.route("/")
def root():
    return {"message": "Room Management Composite Service"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5006, debug=True)
