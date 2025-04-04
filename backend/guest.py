from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from os import environ

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 299}
app.config["JSON_SORT_KEYS"] = False

db = SQLAlchemy(app)

# Guest Model
class Guest (db.Model):
    __tablename__ = "Guest"

    guest_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    contact = db.Column(db.String(15), unique=True, nullable=False)

    def json(self):
        return {
            "guest_id": self.guest_id,
            "name": self.name,
            "email": self.email,
            "contact": self.contact
        }

# Auto-create table if it doesn't exist
with app.app_context():
    db.create_all()

#health check
@app.route("/health")
def health():
    return {"status": "healthy"}

#get all guests
@app.route("/guests", methods=["GET"])
def get_all():
    guest_list = db.session.scalars(db.select(Guest)).all()
    if len(guest_list) > 0: 
        return jsonify({"code": 200, "data": {"guests": [g.json() for g in guest_list]}}), 200
    else:
        return jsonify({"code": 404, "message": "No guests found."}), 404

# get specific guest by ID
@app.route("/guests/<int:guest_id>", methods=["GET"])
def get_guest(guest_id):
    guest = db.session.scalar(db.select(Guest).filter_by(guest_id=guest_id).limit(1)).first()
    
    if guest:
        return jsonify({"code": 200, "data": guest.json()}), 200
    
    return jsonify({"code": 404, "message": "Guest not found."}), 404

#postman example 
#  {
#     "name": "John Doe",
#     "email": "john.doe@example.com",
#     "contact": "91234567"
#  }

#create guests
@app.route("/createGuest", methods=["POST"])
def create_guest():
    data = request.get_json()

    try:
        guest = Guest(**data)
        db.session.add(guest)
        db.session.commit()
        db.session.refresh(guest)
        return jsonify({"code": 201, "data": guest.json()}), 201, {"Location": f"/guests/{guest.guest_id}"}
    except:
        db.session.rollback()
        return jsonify({"code": 500, "data": {"guest_id": guest.guest_id}, "message": f"Error creating guest. "}), 500

#update guest
@app.route("/guests/<int:guest_id>", methods=['PUT'])
def update_guest(guest_id):
    guest = db.session.scalars(db.select(Guest).filter_by(guest_id=guest_id).limit(1)).first()
    if guest:
        data = request.get_json()
        guest.name = data.get("name", guest.name)
        guest.email = data.get("email", guest.email)
        guest.contact = data.get("contact", guest.contact)
        try:
            db.session.commit()
            return jsonify({"code": 200, "data": guest.json()}), 200
        except:
            db.session.rollback()
            return jsonify({"code": 500, "data": {"guest_id": guest.guest_id}, "message": f"Error updating guest. "}), 500
    return jsonify({"code": 404, "message": "Guest not found."}), 404
    
#delete guest
@app.route("/guests/<int:guest_id>", methods=['DELETE'])
def delete_guest(guest_id):
    guest = db.session.scalars(db.select(Guest).filter_by(guest_id=guest_id).limit(1)).first()
    if guest:
        db.session.delete(guest)
        db.session.commit()
        return jsonify({"code": 200, "data": {"guest_id": guest_id}}), 200
    return jsonify({"code": 404, "message": "Guest not found."}), 404
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5011, debug=True)
