# room/main.py
import os
import json
import aio_pika
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import httpx
from prometheus_client import make_asgi_app

import models, schemas
from database import get_db, init_db, run_migrations
from middleware.auth import require_auth, require_auth_security
from middleware.tracking import track_request
from events import publish_event

app = FastAPI(title="Room Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

# Monitoring service configuration
MONITORING_SERVICE_URL = os.getenv("MONITORING_SERVICE_URL", "http://localhost:8001")
TESTING = os.getenv("TESTING") == "true"

# Global variables for RabbitMQ connection
connection = None
channel = None

async def get_rabbitmq_channel():
    global connection, channel
    if not TESTING:
        if not connection or connection.is_closed:
            connection = await aio_pika.connect_robust(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                login=RABBITMQ_USER,
                password=RABBITMQ_PASS
            )
            channel = await connection.channel()
            await channel.declare_exchange("room_events", aio_pika.ExchangeType.TOPIC)
    return channel

async def publish_event(routing_key: str, message: dict):
    if not TESTING:
        channel = await get_rabbitmq_channel()
        exchange = await channel.get_exchange("room_events")
        await exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=routing_key
        )

@app.on_event("startup")
async def startup_event():
    if not TESTING:
        # Initialize RabbitMQ connection
        await get_rabbitmq_channel()
        
        # Initialize room availability metrics via monitoring service
        cursor = get_db()
        query = """
            SELECT room_type, COUNT(*) as count
            FROM rooms
            GROUP BY room_type
        """
        cursor.execute(query)
        async with httpx.AsyncClient() as client:
            for row in cursor.fetchall():
                await client.post(
                    f"{MONITORING_SERVICE_URL}/metrics/room_availability",
                    json={
                        "room_type": row["room_type"],
                        "count": row["count"]
                    }
                )

@app.on_event("shutdown")
async def shutdown_event():
    if not TESTING and connection and not connection.is_closed:
        await connection.close()

@app.post("/rooms/", response_model=schemas.Room)
@require_auth(roles=["admin"])
@track_request()
async def create_room(
    request: Request,
    room: schemas.RoomCreate,
    background_tasks: BackgroundTasks,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Create room
    room_data = {
        "room_number": room.room_number,
        "room_type": room.room_type,
        "price_per_night": room.price_per_night,
        "floor": room.floor
    }
    db_room = models.Room.create(cursor, room_data)
    
    # Track room creation via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "POST",
                    "endpoint": "/rooms/",
                    "count": 1
                }
            )
    
    # Publish room created event
    background_tasks.add_task(
        publish_event,
        "room_created",
        {
            "room_id": db_room["id"],
            "room_number": db_room["room_number"],
            "room_type": db_room["room_type"],
            "price_per_night": str(db_room["price_per_night"]),
            "floor": db_room["floor"],
            "status": db_room["status"]
        }
    )
    
    return db_room

@app.get("/rooms/", response_model=List[schemas.Room])
@require_auth()
@track_request()
async def list_rooms(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    room_type: Optional[models.RoomType] = None,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "GET",
                    "endpoint": "/rooms/",
                    "count": 1
                }
            )
    return models.Room.list_all(cursor, skip=skip, limit=limit)

@app.get("/rooms/availability", response_model=List[schemas.RoomAvailabilityResponse])
@require_auth()
@track_request()
async def get_room_availability(
    request: Request,
    start_date: date,
    end_date: date,
    room_type: Optional[str] = None,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "GET",
                    "endpoint": "/rooms/availability",
                    "count": 1
                }
            )
    
    # Convert room_type string to enum if provided
    room_type_enum = models.RoomType(room_type) if room_type else None
    
    # Get availability for all rooms of the specified type
    return models.RoomAvailability.get_availability_range(
        cursor,
        start_date,
        end_date,
        room_type=room_type_enum
    )

@app.get("/rooms/{room_id}", response_model=schemas.Room)
@require_auth()
@track_request()
async def get_room(
    request: Request,
    room_id: int,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "GET",
                    "endpoint": f"/rooms/{room_id}",
                    "count": 1
                }
            )
    
    room = models.Room.get_by_id(cursor, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

@app.patch("/rooms/{room_id}/status", response_model=schemas.Room)
@require_auth(roles=["admin"])
@track_request()
async def update_room_status(
    request: Request,
    room_id: int,
    status_update: schemas.RoomStatusUpdate,
    background_tasks: BackgroundTasks,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "PATCH",
                    "endpoint": f"/rooms/{room_id}/status",
                    "count": 1
                }
            )
    
    room = models.Room.get_by_id(cursor, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    updated_room = models.Room.update_status(cursor, room_id, status_update.status)
    
    # Publish room status updated event
    background_tasks.add_task(
        publish_event,
        "room_status_updated",
        {
            "room_id": updated_room["id"],
            "room_number": updated_room["room_number"],
            "status": updated_room["status"]
        }
    )
    
    return updated_room

@app.get("/rooms/{room_id}/availability", response_model=bool)
@require_auth()
@track_request()
async def check_room_availability(
    request: Request,
    room_id: int,
    start_date: date,
    end_date: date,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "GET",
                    "endpoint": f"/rooms/{room_id}/availability",
                    "count": 1
                }
            )
    
    room = models.Room.get_by_id(cursor, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return models.Room.check_availability(cursor, room_id, start_date, end_date)

@app.get("/rooms/availability/type/{room_type}", response_model=List[schemas.RoomAvailabilityResponse])
@require_auth()
@track_request()
async def get_room_availability_by_type(
    request: Request,
    room_type: str,
    start_date: date,
    end_date: date,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth_security)
):
    # Track request via monitoring service
    if not TESTING:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{MONITORING_SERVICE_URL}/metrics/request_count",
                json={
                    "method": "GET",
                    "endpoint": f"/rooms/availability/type/{room_type}",
                    "count": 1
                }
            )
    
    try:
        room_type_enum = models.RoomType(room_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid room type")
    
    return models.RoomAvailability.get_by_date_and_type(
        cursor,
        start_date,
        end_date,
        room_type_enum
    )