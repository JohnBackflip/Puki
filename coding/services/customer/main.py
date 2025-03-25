# customer/main.py
from flask import Flask
from flask_cors import CORS
import os
from customer.database import db
from customer.models import Customer  # Ensure models are imported so that they are registered
from customer.routes import customer_bp

app = Flask(__name__)
CORS(app)
app.json.sort_keys = False

#-----------------------#
# Database Configuration
#-----------------------#
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db.init_app(app)


# Initialize the Database (Create Tables)
with app.app_context():
    db.create_all()


app.register_blueprint(customer_bp)


@app.route("/")
def root():
    return {"message": "Customer Management Service"}

@app.route("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
