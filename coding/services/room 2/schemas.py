# room/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from models import RoomType, RoomStatus

class RoomBase(BaseModel):
    room_number: str
    room_type: RoomType
    price_per_night: Decimal = Field(..., ge=0)
    floor: int = Field(..., ge=1)

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    room_type: Optional[RoomType] = None
    price_per_night: Optional[Decimal] = Field(None, ge=0)
    floor: Optional[int] = Field(None, ge=1)
    status: Optional[RoomStatus] = None

class Room(RoomBase):
    id: int
    status: RoomStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RoomAvailability(BaseModel):
    date: date
    room_type: RoomType
    available_count: int = Field(..., ge=0)
    base_price: Decimal = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)

class RoomAvailabilityResponse(BaseModel):
    date: date
    room_type: RoomType
    available_count: int = Field(..., ge=0)
    base_price: Decimal = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)

class RoomStatusUpdate(BaseModel):
    status: RoomStatus

class DateRange(BaseModel):
    start_date: date
    end_date: date

class RoomAvailabilityUpdate(BaseModel):
    date: date
    room_type: RoomType
    available_count: int = Field(..., ge=0)
    base_price: Decimal = Field(..., ge=0)