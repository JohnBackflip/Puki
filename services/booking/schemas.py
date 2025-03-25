# booking/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from services.booking.models import BookingStatus, PaymentStatus, RoomType

class RoomCreate(BaseModel):
    room_number: str
    room_type: RoomType
    price: Decimal = Field(..., ge=0)
    capacity: int = Field(..., gt=0)

class Room(BaseModel):
    id: int
    room_number: str
    room_type: RoomType
    price: Decimal
    capacity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BookingCreate(BaseModel):
    room_id: int
    check_in_date: date
    check_out_date: date
    total_price: Decimal = Field(..., ge=0)
    special_requests: Optional[str] = None

class BookingUpdate(BaseModel):
    status: BookingStatus

class BookingPayment(BaseModel):
    id: int
    booking_id: int
    amount: Decimal
    payment_method: str
    transaction_id: Optional[str]
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Booking(BaseModel):
    id: int
    user_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    status: BookingStatus
    total_price: Decimal
    special_requests: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class BookingWithPayment(Booking):
    payment: Optional[BookingPayment]
    room: Optional[Room]

    class Config:
        orm_mode = True