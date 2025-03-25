from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import RatingValue, ReviewStatus

class ReviewBase(BaseModel):
    booking_id: int
    rating: RatingValue
    comment: str

class ReviewCreate(ReviewBase):
    pass

class ResponseBase(BaseModel):
    comment: str

class ResponseCreate(ResponseBase):
    pass

class Response(ResponseBase):
    id: int
    review_id: int
    staff_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Review(ReviewBase):
    id: int
    user_id: int
    status: ReviewStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    responses: List[Response] = []

    class Config:
        from_attributes = True

class ReviewMetricsBase(BaseModel):
    date: datetime
    average_rating: float
    total_reviews: int
    rating_distribution: str
    sentiment_score: float

class ReviewMetrics(ReviewMetricsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True