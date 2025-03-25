# notification/schemas.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    template_id: str
    data: Dict

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    template_id: str
    data: Dict
    status: NotificationStatus
    sent_at: Optional[datetime]
    error: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True