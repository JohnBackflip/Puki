# housekeeping/schemas.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class CleaningStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"

class CleaningTaskCreate(BaseModel):
    room_id: int
    scheduled_at: datetime
    notes: Optional[str] = None

class CleaningTaskUpdate(BaseModel):
    staff_id: Optional[int] = None
    status: Optional[CleaningStatus] = None
    notes: Optional[str] = None

class CleaningTask(BaseModel):
    id: int
    room_id: int
    staff_id: Optional[int]
    status: CleaningStatus
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True