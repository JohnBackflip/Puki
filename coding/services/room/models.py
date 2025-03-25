from room.database import db

class Room(db.Model):
    __tablename__ = "room"

    room_id = db.Column(db.String(36), primary_key=True)
    room_type = db.Column(db.Enum("Single", "Double", "Family", "PresidentialRooms"), nullable=False)
    status = db.Column(db.Enum("VACANT", "OCCUPIED", "UNAVAI"), default="VACANT")
    room_pin = db.Column(db.String(6), default=None)

    def json(self):
        return {
            "room_id": self.room_id,
            "room_type": self.room_type,
            "status": self.status,
            "room_pin": self.room_pin
        }
