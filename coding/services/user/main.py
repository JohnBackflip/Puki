from flask import Flask
from flask_cors import CORS
import os
from user.database import db
from user.routes import user_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(user_bp)

@app.route("/")
def root():
    return {"message": "User Management Service"}

@app.route("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
