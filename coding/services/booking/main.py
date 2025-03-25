from flask import Flask
from flask_cors import CORS
import os
from booking.database import db
from booking.routes import booking_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# DB config (shared DB)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(booking_bp)

@app.route("/")
def index():
    return {"message": "Booking Microservice"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
