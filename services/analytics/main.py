# analytics/main.py
from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List, Dict
import httpx
from datetime import datetime, date, timedelta
import pandas as pd
from prometheus_client import make_asgi_app
import os

from . import models, schemas, database, events
from .database import engine
from middleware.auth import require_auth
from monitoring.prometheus import track_request, REQUEST_COUNT
from monitoring.tracing import setup_tracing

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
setup_tracing(app, "analytics-service")

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

event_consumer = events.EventConsumer()

@app.on_event("startup")
async def startup_event():
    await event_consumer.connect()
    
    async def handle_booking_events(data: dict):
        # Update metrics when bookings are created/updated
        db = next(database.get_db())
        today = datetime.now().date()
        
        metrics = db.query(models.BookingMetrics).filter(
            models.BookingMetrics.date == today
        ).first()
        
        if not metrics:
            metrics = models.BookingMetrics(
                date=today,
                total_bookings=0,
                total_revenue=0,
                occupancy_rate=0,
                avg_stay_duration=0
            )
            db.add(metrics)
        
        # Update metrics based on event type
        if data["event_type"] == "booking.created":
            metrics.total_bookings += 1
            metrics.total_revenue += data["amount"]
        
        db.commit()
    
    await event_consumer.subscribe("booking.*", handle_booking_events)

@app.get("/metrics/bookings", response_model=List[schemas.MetricsResponse])
@require_auth(roles=["staff", "admin"])
async def get_booking_metrics(
    date_range: schemas.DateRange,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    metrics = db.query(models.BookingMetrics).filter(
        models.BookingMetrics.date >= date_range.start_date,
        models.BookingMetrics.date <= date_range.end_date
    ).all()
    
    return metrics

@app.get("/metrics/rooms/{room_id}", response_model=List[schemas.RoomMetricsResponse])
@require_auth(roles=["staff", "admin"])
async def get_room_metrics(
    room_id: int,
    date_range: schemas.DateRange,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    metrics = db.query(models.RoomMetrics).filter(
        models.RoomMetrics.room_id == room_id,
        models.RoomMetrics.date >= date_range.start_date,
        models.RoomMetrics.date <= date_range.end_date
    ).all()
    
    return metrics

@app.get("/reports/revenue")
@require_auth(roles=["admin"])
async def generate_revenue_report(
    date_range: schemas.DateRange,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get booking metrics
    metrics = pd.DataFrame([
        {
            "date": m.date,
            "revenue": m.total_revenue,
            "bookings": m.total_bookings,
            "occupancy": m.occupancy_rate
        }
        for m in db.query(models.BookingMetrics).filter(
            models.BookingMetrics.date >= date_range.start_date,
            models.BookingMetrics.date <= date_range.end_date
        ).all()
    ])
    
    if metrics.empty:
        raise HTTPException(status_code=404, detail="No data found for date range")
    
    # Calculate key metrics
    total_revenue = metrics["revenue"].sum()
    avg_daily_revenue = metrics["revenue"].mean()
    avg_occupancy = metrics["occupancy"].mean()
    
    return {
        "total_revenue": total_revenue,
        "avg_daily_revenue": avg_daily_revenue,
        "avg_occupancy_rate": avg_occupancy,
        "daily_breakdown": metrics.to_dict(orient="records")
    }

@app.get("/analytics/customer-segments")
@require_auth(roles=["admin"])
@track_request()
async def get_customer_segments(
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get customer data from booking history
    customer_data = []
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://booking:8006/bookings/statistics/by-user",
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
        )
        customer_data = response.json()
    
    # Call ML service for customer segmentation
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml_service:8000/predict/customer-segments",
            json={"customers": customer_data}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ML service error")
        
        segments_data = response.json()
        
        # Combine results
        for customer, segment in zip(customer_data, segments_data["segments"]):
            customer['segment'] = segment
    
    return {
        "segments": segments_data["segment_descriptions"],
        "customers": customer_data
    }

@app.post("/analytics/predict/revenue")
@require_auth(roles=["admin"])
@track_request()
async def predict_revenue(
    features: Dict,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Call ML service for revenue prediction
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml_service:8000/predict/revenue",
            json=features
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ML service error")
        
        prediction = response.json()
    
    return prediction

@app.get("/analytics/predict/maintenance")
@require_auth(roles=["admin", "maintenance"])
@track_request()
async def predict_maintenance_needs(
    room_id: int,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get room data
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://room:8002/rooms/{room_id}/statistics",
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room_data = response.json()
    
    # Call ML service for maintenance prediction
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml_service:8000/predict/maintenance",
            json={
                "room_id": room_id,
                "last_maintenance_days": room_data["days_since_maintenance"],
                "occupancy_rate": room_data["occupancy_rate"],
                "reported_issues": room_data["reported_issues"],
                "age_in_years": room_data["age_in_years"]
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ML service error")
        
        prediction = response.json()
    
    return {
        "room_id": room_id,
        "maintenance_needed": prediction["needs_maintenance"],
        "confidence": prediction["confidence"],
        "recommended_date": (
            datetime.now() + timedelta(days=7)
        ).isoformat() if prediction["needs_maintenance"] else None,
        "factors": prediction["contributing_factors"]
    }

@app.get("/analytics/predict/staff-assignment")
@require_auth(roles=["admin", "staff"])
@track_request()
async def predict_staff_assignment(
    date: date,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get staff and room data
    async with httpx.AsyncClient() as client:
        staff_response = await client.get(
            "http://staff:8003/staff/available",
            params={"date": date.isoformat()},
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
        )
        room_response = await client.get(
            "http://housekeeping:8007/tasks/pending",
            params={"date": date.isoformat()},
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
        )
        
        if staff_response.status_code != 200 or room_response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error fetching data")
        
        staff_data = staff_response.json()
        room_data = room_response.json()
    
    # Call ML service for staff assignment prediction
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml_service:8000/predict/staff-assignment",
            json={
                "staff": staff_data,
                "rooms": room_data,
                "date": date.isoformat()
            }
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ML service error")
        
        assignments = response.json()
    
    return assignments

@app.get("/analytics/trends")
@require_auth(roles=["admin"])
@track_request()
async def analyze_trends(
    date_range: schemas.DateRange,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get metrics data
    metrics = pd.DataFrame([
        {
            "date": m.date,
            "revenue": m.total_revenue,
            "bookings": m.total_bookings,
            "occupancy": m.occupancy_rate
        }
        for m in db.query(models.BookingMetrics).filter(
            models.BookingMetrics.date >= date_range.start_date,
            models.BookingMetrics.date <= date_range.end_date
        ).all()
    ])
    
    if metrics.empty:
        raise HTTPException(status_code=404, detail="No data found for date range")
    
    # Call ML service for trend analysis
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml_service:8000/analyze/trends",
            json=metrics.to_dict(orient="records")
        )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="ML service error")
        
        trend_analysis = response.json()
    
    return {
        **trend_analysis,
        "raw_metrics": metrics.to_dict(orient="records")
    }