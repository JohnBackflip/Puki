import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
import httpx
from prometheus_client import make_asgi_app
import strawberry
from strawberry.fastapi import GraphQLRouter


from services.booking import models, schemas
from services.booking.database import get_db, init_db, run_migrations
from services.booking.graphql_schema import schema
from services.room.middleware.auth import require_auth, require_auth_security
from services.monitoring.prometheus import ACTIVE_BOOKINGS
from services.monitoring.tracing import setup_tracing


# Application Initialization 
app = FastAPI(title="Booking Service")
setup_tracing(app, "booking-service")

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize database and run migrations (integrated from your original setup)
init_db()
run_migrations()

# GraphQL Endpoint Setup
async def get_context(request: Request) -> Dict[str, Any]:
    return {"request": request, "db": get_db()}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

#----------------------------#
# REST Endpoints - Rooms
#----------------------------#
@app.post("/rooms", response_model=schemas.Room)
@require_auth(["admin"])
async def create_room(
    room: schemas.RoomCreate,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        try:
            result = models.Room.create(cursor, room.room_number, room.room_type, room.price, room.capacity)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            if "Duplicate entry" in str(e):
                raise HTTPException(status_code=400, detail="Room number already exists")
            raise

@app.get("/rooms", response_model=List[schemas.Room])
async def list_rooms(
    room_type: Optional[models.RoomType] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_capacity: Optional[int] = None,
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        return models.Room.list_rooms(cursor, room_type, min_price, max_price, min_capacity)

@app.get("/rooms/{room_id}", response_model=schemas.Room)
async def get_room(room_id: int, db = Depends(get_db)):
    with db.cursor() as cursor:
        room = models.Room.get_by_id(cursor, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room

#-------------------------------#
# REST Endpoints - Bookings (Creation, Listing, Retrieval)
# (Integrated booking creation now accepts a new field: customer_id)
#-------------------------------#
@app.post("/bookings", response_model=schemas.BookingWithPayment)
@require_auth()
async def create_booking(
    booking: schemas.BookingCreate,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        # Check if room exists
        room = models.Room.get_by_id(cursor, booking.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Check room availability
        if not models.Booking.check_availability(cursor, booking.room_id, booking.check_in_date, booking.check_out_date):
            raise HTTPException(status_code=400, detail="Room not available for these dates")
        
        try:
            result = models.Booking.create(
                cursor,
                user_data["user_id"],
                booking.customer_id,  # New customer_id field integrated here
                booking.room_id,
                booking.check_in_date,
                booking.check_out_date,
                booking.total_price,
                booking.special_requests
            )
            db.commit()
            ACTIVE_BOOKINGS.inc()  # Integrated metrics update
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings", response_model=List[schemas.BookingWithPayment])
@require_auth()
async def list_bookings(
    skip: int = 0,
    limit: int = 100,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        return models.Booking.list_by_user(cursor, user_data["user_id"], skip, limit)

@app.get("/bookings/{booking_id}", response_model=schemas.BookingWithPayment)
@require_auth()
async def get_booking(
    booking_id: int,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        booking = models.Booking.get_by_id(cursor, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking["user_id"] != user_data["user_id"] and "admin" not in user_data["scopes"]:
            raise HTTPException(status_code=403, detail="Not authorized to view this booking")
        return booking

#---------------------------------#
# REST Endpoints - Booking Check-In/Check-Out & Cancellation
#---------------------------------#
@app.post("/bookings/{booking_id}/check-in", response_model=schemas.BookingWithPayment)
@require_auth()
async def check_in(
    booking_id: int,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        booking = models.Booking.get_by_id(cursor, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking["user_id"] != user_data["user_id"] and "admin" not in user_data["scopes"]:
            raise HTTPException(status_code=403, detail="Not authorized to check in this booking")
        if booking["status"] != models.BookingStatus.CONFIRMED.value:
            raise HTTPException(status_code=400, detail="Booking must be confirmed before check-in")
        try:
            result = models.Booking.update_status(cursor, booking_id, models.BookingStatus.CHECKED_IN)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/bookings/{booking_id}/check-out", response_model=schemas.BookingWithPayment)
@require_auth()
async def check_out(
    booking_id: int,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        booking = models.Booking.get_by_id(cursor, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking["user_id"] != user_data["user_id"] and "admin" not in user_data["scopes"]:
            raise HTTPException(status_code=403, detail="Not authorized to check out this booking")
        if booking["status"] != models.BookingStatus.CHECKED_IN.value:
            raise HTTPException(status_code=400, detail="Booking must be checked in before check-out")
        try:
            result = models.Booking.update_status(cursor, booking_id, models.BookingStatus.CHECKED_OUT)
            db.commit()
            ACTIVE_BOOKINGS.dec()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/bookings/{booking_id}/cancel", response_model=schemas.BookingWithPayment)
@require_auth()
async def cancel_booking(
    booking_id: int,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        booking = models.Booking.get_by_id(cursor, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        if booking["user_id"] != user_data["user_id"] and "admin" not in user_data["scopes"]:
            raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
        try:
            result = models.Booking.cancel_booking(cursor, booking_id)
            if not result:
                raise HTTPException(status_code=400, detail="Cannot cancel booking in current state")
            db.commit()
            if booking["status"] in [models.BookingStatus.CONFIRMED.value, models.BookingStatus.CHECKED_IN.value]:
                ACTIVE_BOOKINGS.dec()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

#-----------------------#
# REST Endpoint - Room Availability
#-----------------------#
@app.get("/rooms/{room_id}/availability")
async def check_room_availability(
    room_id: int,
    check_in: date = Query(...),
    check_out: date = Query(...),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        room = models.Room.get_by_id(cursor, room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        is_available = models.Booking.check_availability(cursor, room_id, check_in, check_out)
        return {"available": is_available}


# Root & Health Endpoints
@app.get("/")
async def root():
    return {"message": "Booking Service with GraphQL API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Application Runner
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
