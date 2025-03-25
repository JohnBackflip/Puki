from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Gauge, make_asgi_app
from pydantic import BaseModel
from typing import Dict, Optional
import os

app = FastAPI(title="Monitoring Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint']
)

ROOM_AVAILABILITY = Gauge(
    'room_availability',
    'Number of available rooms by type',
    ['room_type']
)

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

class RequestCount(BaseModel):
    method: str
    endpoint: str
    count: int

class RoomAvailability(BaseModel):
    room_type: str
    count: int

@app.post("/metrics/request_count")
async def update_request_count(data: RequestCount):
    try:
        REQUEST_COUNT.labels(
            method=data.method,
            endpoint=data.endpoint
        ).inc(data.count)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/metrics/room_availability")
async def update_room_availability(data: RoomAvailability):
    try:
        ROOM_AVAILABILITY.labels(room_type=data.room_type).set(data.count)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 