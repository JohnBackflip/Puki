import enum
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal

class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class RoomType(enum.Enum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"

class Room:
    @staticmethod
    def create(cursor, room_number: str, room_type: RoomType, price: Decimal, capacity: int) -> Dict[str, Any]:
        query = """
            INSERT INTO rooms (room_number, room_type, price, capacity)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (room_number, room_type.value, price, capacity))
        cursor.execute("SELECT LAST_INSERT_ID()")
        room_id = cursor.fetchone()["LAST_INSERT_ID()"]
        return Room.get_by_id(cursor, room_id)

    @staticmethod
    def get_by_id(cursor, room_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM rooms WHERE id = %s"
        cursor.execute(query, (room_id,))
        return cursor.fetchone()

    @staticmethod
    def list_rooms(cursor, room_type: Optional[RoomType] = None, min_price: Optional[float] = None,
                   max_price: Optional[float] = None, min_capacity: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM rooms WHERE 1=1"
        params = []
        if room_type:
            query += " AND room_type = %s"
            params.append(room_type.value)
        if min_price is not None:
            query += " AND price >= %s"
            params.append(min_price)
        if max_price is not None:
            query += " AND price <= %s"
            params.append(max_price)
        if min_capacity is not None:
            query += " AND capacity >= %s"
            params.append(min_capacity)
        cursor.execute(query, tuple(params))
        return cursor.fetchall()

class Booking:
    @staticmethod
    def create(cursor, user_id: int, customer_id: int, room_id: int, check_in_date: date, 
               check_out_date: date, total_price: Decimal, 
               special_requests: Optional[str] = None) -> Dict[str, Any]:
        query = """
            INSERT INTO bookings 
                (user_id, customer_id, room_id, check_in_date, check_out_date, total_price, special_requests)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, customer_id, room_id, check_in_date, check_out_date,
                                 total_price, special_requests))
        cursor.execute("SELECT LAST_INSERT_ID()")
        booking_id = cursor.fetchone()["LAST_INSERT_ID()"]
        return Booking.get_by_id(cursor, booking_id)

    @staticmethod
    def get_by_id(cursor, booking_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT b.*, p.status as payment_status, p.transaction_id, r.*
            FROM bookings b
            LEFT JOIN booking_payments p ON b.id = p.booking_id
            LEFT JOIN rooms r ON b.room_id = r.id
            WHERE b.id = %s
        """
        cursor.execute(query, (booking_id,))
        return cursor.fetchone()

    @staticmethod
    def list_by_user(cursor, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT b.*, p.status as payment_status, p.transaction_id, r.*
            FROM bookings b
            LEFT JOIN booking_payments p ON b.id = p.booking_id
            LEFT JOIN rooms r ON b.room_id = r.id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, limit, skip))
        return cursor.fetchall()

    @staticmethod
    def update_status(cursor, booking_id: int, status: BookingStatus) -> Optional[Dict[str, Any]]:
        query = "UPDATE bookings SET status = %s WHERE id = %s"
        cursor.execute(query, (status.value, booking_id))
        return Booking.get_by_id(cursor, booking_id) if cursor.rowcount > 0 else None

    @staticmethod
    def cancel_booking(cursor, booking_id: int) -> Optional[Dict[str, Any]]:
        booking = Booking.get_by_id(cursor, booking_id)
        if not booking or booking["status"] in [BookingStatus.CHECKED_IN.value, BookingStatus.CHECKED_OUT.value]:
            return None
        return Booking.update_status(cursor, booking_id, BookingStatus.CANCELLED)

    @staticmethod
    def check_availability(cursor, room_id: int, check_in: date, check_out: date) -> bool:
        query = """
            SELECT COUNT(*) as count
            FROM bookings
            WHERE room_id = %s
            AND status NOT IN ('cancelled', 'checked_out')
            AND (
                (check_in_date <= %s AND check_out_date > %s) OR
                (check_in_date < %s AND check_out_date >= %s) OR
                (check_in_date >= %s AND check_in_date < %s)
            )
        """
        cursor.execute(query, (room_id, check_out, check_in, check_out, check_out, check_in, check_out))
        result = cursor.fetchone()
        return result["count"] == 0

class BookingPayment:
    @staticmethod
    def create(cursor, booking_id: int, amount: Decimal, 
              payment_method: str, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        query = """
            INSERT INTO booking_payments 
                (booking_id, amount, payment_method, transaction_id)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (booking_id, amount, payment_method, transaction_id))
        cursor.execute("SELECT LAST_INSERT_ID()")
        payment_id = cursor.fetchone()["LAST_INSERT_ID()"]
        return BookingPayment.get_by_id(cursor, payment_id)

    @staticmethod
    def get_by_id(cursor, payment_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM booking_payments WHERE id = %s"
        cursor.execute(query, (payment_id,))
        return cursor.fetchone()

    @staticmethod
    def update_status(cursor, payment_id: int, status: PaymentStatus, 
                     transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        query = """
            UPDATE booking_payments 
            SET status = %s, transaction_id = %s 
            WHERE id = %s
        """
        cursor.execute(query, (status.value, transaction_id, payment_id))
        return BookingPayment.get_by_id(cursor, payment_id) if cursor.rowcount > 0 else None
