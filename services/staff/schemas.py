# staff/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum
from typing import Optional, List

class StaffRole(str, Enum):
    MANAGER = "manager"
    RECEPTIONIST = "receptionist"
    HOUSEKEEPER = "housekeeper"
    MAINTENANCE = "maintenance"

class ShiftBase(BaseModel):
    start_time: datetime
    end_time: datetime

class ShiftCreate(ShiftBase):
    staff_id: int

class Shift(ShiftBase):
    id: int
    staff_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class StaffBase(BaseModel):
    name: str
    email: EmailStr
    role: StaffRole

class StaffCreate(StaffBase):
    pass

class Staff(StaffBase):
    id: int
    created_at: datetime
    shifts: List[Shift] = []
    
    class Config:
        from_attributes = True