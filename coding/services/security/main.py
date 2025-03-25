from flask import Flask
from flask_cors import CORS
import os
from security.database import db
from security.models import Keycard
from security.routes import security_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(security_bp)

@app.route("/")
def root():
    return {"message": "Security Service (Keycard Management)"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
