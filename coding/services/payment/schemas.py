# payment/schemas.py
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"

class PaymentCreate(BaseModel):
    booking_id: int
    amount: float
    currency: str = "USD"
    payment_method: PaymentMethod

class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: PaymentMethod
    payment_intent_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True