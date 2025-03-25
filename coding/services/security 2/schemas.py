# security/schemas.py
from pydantic import BaseModel
from datetime import datetime

class KeyCreate(BaseModel):
    booking_id: int
    room_id: int
    valid_until: datetime

class KeyResponse(BaseModel):
    id: int
    key_hash: str
    valid_from: datetime
    valid_until: datetime
    is_active: bool
    
    class Config:
        from_attributes = True