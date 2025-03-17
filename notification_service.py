from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
CORS(app)

app.json.sort_keys = False 

app.config["SQLALCHEMY_DATABASE_URI"] = (
    environ.get("dbURL") or "mysql+mysqlconnector://root@localhost:3306/puki"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}

db = SQLAlchemy(app)


class Notification(db.Model):
    __tablename__ = "notification"

    notification_id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    def json(self):
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "message": self.message,
        }


@app.route("/notifications")
def get_all_notifications():
    notificationlist = db.session.scalars(db.select(Notification)).all()
    if notificationlist:
        return jsonify({"code": 200, "data": {"notifications": [n.json() for n in notificationlist]}})
    return jsonify({"code": 404, "message": "No notifications found."}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)
