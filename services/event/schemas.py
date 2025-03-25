from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from services.event.models import EventType, PriceAdjustmentType

class EventBase(BaseModel):
    name: str
    description: str
    event_type: str
    start_date: datetime
    end_date: datetime
    location: str

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PriceAdjustmentBase(BaseModel):
    event_id: int
    adjustment_type: str
    value: float

class PriceAdjustmentCreate(PriceAdjustmentBase):
    pass

class PriceAdjustmentUpdate(BaseModel):
    adjustment_type: str
    value: float

class PriceAdjustment(PriceAdjustmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PriceCalculationRequest(BaseModel):
    room_type: str
    base_price: float
    check_in_date: datetime
    check_out_date: datetime

class PriceCalculationResponse(BaseModel):
    original_price: float
    adjusted_price: float
    adjustments: List[PriceAdjustment] 