# security/models.py
from datetime import datetime
from security.database import db

class Keycard(db.Model):
    __tablename__ = "keycard"

    keycard_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_id = db.Column(db.Integer, nullable=False, unique=True)
    user_id = db.Column(db.Integer, nullable=True)
    customer_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.String(36), nullable=False)
    key_pin = db.Column(db.String(6), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def json(self):
        return {
            "keycard_id": self.keycard_id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "room_id": self.room_id,
            "key_pin": self.key_pin,
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
