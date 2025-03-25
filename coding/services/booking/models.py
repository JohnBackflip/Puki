from booking.database import db

class Booking(db.Model):
    __tablename__ = "booking"

    booking_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    room_id = db.Column(db.String(36), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum("CONFIRMED", "CANCELLED", "CHECKED-IN", "CHECKED-OUT"), default="CONFIRMED")

    def json(self):
        return {
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "customer_id": self.customer_id,
            "room_id": self.room_id,
            "check_in_date": self.check_in_date.isoformat(),
            "check_out_date": self.check_out_date.isoformat(),
            "status": self.status
        }
