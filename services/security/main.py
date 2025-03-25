# security/main.py
from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
import secrets
from datetime import datetime

from . import models, schemas, database
from .database import engine
from middleware.auth import require_auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def generate_key_hash():
    return secrets.token_urlsafe(32)

@app.post("/keys/", response_model=schemas.KeyResponse)
@require_auth(roles=["staff", "admin"])
async def create_key(
    key: schemas.KeyCreate,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Deactivate any existing keys for this booking
    existing_keys = db.query(models.DigitalKey).filter(
        models.DigitalKey.booking_id == key.booking_id,
        models.DigitalKey.is_active == True
    ).all()
    
    for existing_key in existing_keys:
        existing_key.is_active = False
    
    # Create new key
    db_key = models.DigitalKey(
        booking_id=key.booking_id,
        room_id=key.room_id,
        key_hash=generate_key_hash(),
        valid_from=datetime.now(),
        valid_until=key.valid_until,
        is_active=True
    )
    
    db.add(db_key)
    db.commit()
    db.refresh(db_key)
    return db_key

@app.post("/keys/validate")
@require_auth()
async def validate_key(
    key_hash: str,
    room_id: int,
    db: Session = Depends(database.get_db)
):
    key = db.query(models.DigitalKey).filter(
        models.DigitalKey.key_hash == key_hash,
        models.DigitalKey.room_id == room_id,
        models.DigitalKey.is_active == True
    ).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="Invalid key")
    
    now = datetime.now()
    if now < key.valid_from or now > key.valid_until:
        raise HTTPException(status_code=400, detail="Key expired")
    
    return {"valid": True}

@app.delete("/keys/booking/{booking_id}")
@require_auth(roles=["staff", "admin"])
async def deactivate_keys(
    booking_id: int,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    keys = db.query(models.DigitalKey).filter(
        models.DigitalKey.booking_id == booking_id,
        models.DigitalKey.is_active == True
    ).all()
    
    for key in keys:
        key.is_active = False
    
    db.commit()
    return {"status": "deactivated"}