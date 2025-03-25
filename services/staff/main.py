# staff/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import asyncio

from . import models, schemas, database, events
from .database import engine
from middleware.auth import require_auth  # Import the middleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
event_publisher = events.EventPublisher()
event_consumer = events.EventConsumer()

@app.on_event("startup")
async def startup_event():
    await event_publisher.connect()
    await event_consumer.connect()
    
    async def handle_room_cleaned(data: dict):
        # Update housekeeping staff schedule
        pass
    
    await event_consumer.subscribe("room.cleaned", handle_room_cleaned)

@app.post("/staff/", response_model=schemas.Staff)
def create_staff(staff: schemas.StaffCreate, db: Session = Depends(database.get_db)):
    db_staff = models.Staff(**staff.dict())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

@app.get("/staff/", response_model=List[schemas.Staff])
def list_staff(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    staff = db.query(models.Staff).offset(skip).limit(limit).all()
    return staff

@app.post("/shifts/", response_model=schemas.Shift)
async def create_shift(shift: schemas.ShiftCreate, db: Session = Depends(database.get_db)):
    db_shift = models.Shift(**shift.dict())
    db.add(db_shift)
    db.commit()
    db.refresh(db_shift)
    
    # Publish event
    await event_publisher.publish(
        "staff.shift.created",
        {
            "staff_id": shift.staff_id,
            "start_time": shift.start_time.isoformat(),
            "end_time": shift.end_time.isoformat()
        }
    )
    
    return db_shift

@app.get("/staff/{staff_id}/shifts/", response_model=List[schemas.Shift])
def get_staff_shifts(staff_id: int, db: Session = Depends(database.get_db)):
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    return staff.shifts