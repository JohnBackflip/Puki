# analytics/schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

class MetricsResponse(BaseModel):
    date: date
    total_bookings: int
    total_revenue: float
    occupancy_rate: float
    avg_stay_duration: float
    
    class Config:
        from_attributes = True

class RoomMetricsResponse(BaseModel):
    room_id: int
    date: date
    occupancy_rate: float
    revenue: float
    cleaning_time_avg: float
    maintenance_count: int
    
    class Config:
        from_attributes = True

class DateRange(BaseModel):
    start_date: date
    end_date: date