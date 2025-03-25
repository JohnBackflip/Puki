"""
Script to run the booking service with GraphQL support.
"""
import os
import sys
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from datetime import date, datetime
from decimal import Decimal
import strawberry
from strawberry.fastapi import GraphQLRouter
import uuid
import json
from enum import Enum

# Set up FastAPI app
app = FastAPI(title="Booking Service")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you should specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory data store
class InMemoryDB:
    def __init__(self):
        self.bookings = {}
        self.payments = {}
        self.booking_counter = 1
        self.payment_counter = 1
        
        # Add some sample data
        self._add_sample_data()
    
    def _add_sample_data(self):
        # Sample bookings
        booking1 = {
            "id": self.booking_counter,
            "user_id": 1,
            "room_id": 101,
            "check_in_date": date(2025, 4, 1),
            "check_out_date": date(2025, 4, 5),
            "status": "confirmed",
            "total_price": Decimal("500.00"),
            "special_requests": "Early check-in requested",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "payment_status": "paid",
            "transaction_id": "txn_" + str(uuid.uuid4())[:8]
        }
        self.bookings[self.booking_counter] = booking1
        self.booking_counter += 1
        
        booking2 = {
            "id": self.booking_counter,
            "user_id": 2,
            "room_id": 102,
            "check_in_date": date(2025, 4, 10),
            "check_out_date": date(2025, 4, 15),
            "status": "pending",
            "total_price": Decimal("750.00"),
            "special_requests": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "payment_status": "pending",
            "transaction_id": None
        }
        self.bookings[self.booking_counter] = booking2
        self.booking_counter += 1
        
        booking3 = {
            "id": self.booking_counter,
            "user_id": 1,
            "room_id": 103,
            "check_in_date": date(2025, 3, 20),
            "check_out_date": date(2025, 3, 25),
            "status": "checked_in",
            "total_price": Decimal("600.00"),
            "special_requests": "Extra towels",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "payment_status": "paid",
            "transaction_id": "txn_" + str(uuid.uuid4())[:8]
        }
        self.bookings[self.booking_counter] = booking3
        self.booking_counter += 1

# Create in-memory database
db = InMemoryDB()

# Booking status and payment status enums
class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

# Booking model with in-memory operations
class Booking:
    @staticmethod
    async def create(user_id: int, room_id: int, check_in_date: date, 
                    check_out_date: date, total_price: Decimal, 
                    special_requests: Optional[str] = None) -> Dict[str, Any]:
        """Create a new booking."""
        booking_id = db.booking_counter
        booking = {
            "id": booking_id,
            "user_id": user_id,
            "room_id": room_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "status": BookingStatus.PENDING.value,
            "total_price": total_price,
            "special_requests": special_requests,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "payment_status": PaymentStatus.PENDING.value,
            "transaction_id": None
        }
        
        db.bookings[booking_id] = booking
        db.booking_counter += 1
        
        return booking
    
    @staticmethod
    async def get_by_id(booking_id: int) -> Optional[Dict[str, Any]]:
        """Get a booking by ID."""
        return db.bookings.get(booking_id)
    
    @staticmethod
    async def update(booking_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a booking."""
        if not updates or booking_id not in db.bookings:
            return None
        
        booking = db.bookings[booking_id]
        
        # Update fields
        for key, value in updates.items():
            booking[key] = value
        
        # Update timestamp
        booking["updated_at"] = datetime.now()
        
        return booking
    
    @staticmethod
    async def update_status(booking_id: int, status: str) -> Optional[Dict[str, Any]]:
        """Update booking status."""
        if booking_id not in db.bookings:
            return None
        
        booking = db.bookings[booking_id]
        booking["status"] = status
        booking["updated_at"] = datetime.now()
        
        return booking
    
    @staticmethod
    async def cancel_booking(booking_id: int) -> Optional[Dict[str, Any]]:
        """Cancel a booking."""
        if booking_id not in db.bookings:
            return None
        
        booking = db.bookings[booking_id]
        
        # Check if booking can be cancelled
        if booking["status"] in [BookingStatus.CHECKED_OUT.value, BookingStatus.CANCELLED.value]:
            return None
        
        # Update booking status
        booking["status"] = BookingStatus.CANCELLED.value
        booking["updated_at"] = datetime.now()
        
        return booking
        
    @staticmethod
    async def list_bookings(user_id: Optional[int] = None, status: Optional[str] = None, 
                          skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List bookings with optional filters."""
        bookings = list(db.bookings.values())
        
        # Apply filters
        if user_id is not None:
            bookings = [b for b in bookings if b["user_id"] == user_id]
        
        if status is not None:
            bookings = [b for b in bookings if b["status"] == status]
        
        # Sort by created_at (newest first)
        bookings.sort(key=lambda b: b["created_at"], reverse=True)
        
        # Apply pagination
        return bookings[skip:skip+limit]

# GraphQL types
@strawberry.type
class BookingType:
    id: int
    user_id: int = strawberry.field(name="user_id")
    room_id: int = strawberry.field(name="room_id")
    check_in_date: date = strawberry.field(name="check_in_date")
    check_out_date: date = strawberry.field(name="check_out_date")
    status: str
    payment_status: Optional[str] = strawberry.field(name="payment_status")
    total_price: float = strawberry.field(name="total_price")
    special_requests: Optional[str] = strawberry.field(name="special_requests")
    created_at: datetime = strawberry.field(name="created_at")
    updated_at: datetime = strawberry.field(name="updated_at")
    transaction_id: Optional[str] = strawberry.field(default=None, name="transaction_id")

# Input types
@strawberry.input
class BookingCreateInput:
    user_id: int = strawberry.field(name="user_id")
    room_id: int = strawberry.field(name="room_id")
    check_in_date: date = strawberry.field(name="check_in_date")
    check_out_date: date = strawberry.field(name="check_out_date")
    total_price: float = strawberry.field(name="total_price")
    special_requests: Optional[str] = strawberry.field(name="special_requests", default=None)

@strawberry.input
class BookingUpdateInput:
    check_in_date: Optional[date] = strawberry.field(name="check_in_date", default=None)
    check_out_date: Optional[date] = strawberry.field(name="check_out_date", default=None)
    special_requests: Optional[str] = strawberry.field(name="special_requests", default=None)

# GraphQL queries
@strawberry.type
class Query:
    @strawberry.field
    async def booking(self, info, id: int) -> Optional[BookingType]:
        booking_data = await Booking.get_by_id(id)
        if not booking_data:
            return None
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=booking_data["id"],
            user_id=booking_data["user_id"],
            room_id=booking_data["room_id"],
            check_in_date=booking_data["check_in_date"],
            check_out_date=booking_data["check_out_date"],
            status=booking_data["status"],
            payment_status=booking_data["payment_status"],
            total_price=booking_data["total_price"],
            special_requests=booking_data.get("special_requests"),
            created_at=booking_data["created_at"],
            updated_at=booking_data["updated_at"],
            transaction_id=booking_data.get("transaction_id")
        )

    @strawberry.field
    async def bookings(
        self, 
        info, 
        user_id: Optional[int] = None, 
        status: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[BookingType]:
        bookings_data = await Booking.list_bookings(user_id, status, skip, limit)
        
        # Convert snake_case to camelCase for each booking
        result = []
        for booking in bookings_data:
            # Convert Decimal to float for total_price
            total_price = float(booking["total_price"])
            
            booking_type = BookingType(
                id=booking["id"],
                user_id=booking["user_id"],
                room_id=booking["room_id"],
                check_in_date=booking["check_in_date"],
                check_out_date=booking["check_out_date"],
                status=booking["status"],
                payment_status=booking["payment_status"],
                total_price=total_price,
                special_requests=booking.get("special_requests"),
                created_at=booking["created_at"],
                updated_at=booking["updated_at"],
                transaction_id=booking.get("transaction_id")
            )
            result.append(booking_type)
        
        return result

# GraphQL mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_booking(self, info, booking: BookingCreateInput) -> BookingType:
        # Convert to Decimal for database
        total_price = Decimal(str(booking.total_price))
        
        # Create booking
        booking_data = await Booking.create(
            booking.user_id,
            booking.room_id,
            booking.check_in_date,
            booking.check_out_date,
            total_price,
            booking.special_requests
        )
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=booking_data["id"],
            user_id=booking_data["user_id"],
            room_id=booking_data["room_id"],
            check_in_date=booking_data["check_in_date"],
            check_out_date=booking_data["check_out_date"],
            status=booking_data["status"],
            payment_status=booking_data["payment_status"],
            total_price=booking_data["total_price"],
            special_requests=booking_data.get("special_requests"),
            created_at=booking_data["created_at"],
            updated_at=booking_data["updated_at"],
            transaction_id=booking_data.get("transaction_id")
        )

    @strawberry.mutation
    async def update_booking(self, info, id: int, booking: BookingUpdateInput) -> Optional[BookingType]:
        # Check if booking exists
        existing = await Booking.get_by_id(id)
        if not existing:
            return None
        
        # Update fields
        updates = {}
        if booking.check_in_date:
            updates["check_in_date"] = booking.check_in_date
        if booking.check_out_date:
            updates["check_out_date"] = booking.check_out_date
        if booking.special_requests is not None:
            updates["special_requests"] = booking.special_requests
        
        if not updates:
            # Convert snake_case to camelCase for GraphQL response
            return BookingType(
                id=existing["id"],
                user_id=existing["user_id"],
                room_id=existing["room_id"],
                check_in_date=existing["check_in_date"],
                check_out_date=existing["check_out_date"],
                status=existing["status"],
                payment_status=existing["payment_status"],
                total_price=existing["total_price"],
                special_requests=existing.get("special_requests"),
                created_at=existing["created_at"],
                updated_at=existing["updated_at"],
                transaction_id=existing.get("transaction_id")
            )
        
        # Perform update
        updated = await Booking.update(id, updates)
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=updated["id"],
            user_id=updated["user_id"],
            room_id=updated["room_id"],
            check_in_date=updated["check_in_date"],
            check_out_date=updated["check_out_date"],
            status=updated["status"],
            payment_status=updated["payment_status"],
            total_price=updated["total_price"],
            special_requests=updated.get("special_requests"),
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
            transaction_id=updated.get("transaction_id")
        )

    @strawberry.mutation
    async def check_in_booking(self, info, id: int) -> Optional[BookingType]:
        # Get booking
        booking = await Booking.get_by_id(id)
        if not booking:
            return None
        
        # Check booking status
        if booking["status"] != BookingStatus.CONFIRMED.value:
            return None
        
        # Update booking status
        updated_booking = await Booking.update_status(
            id,
            BookingStatus.CHECKED_IN.value
        )
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=updated_booking["id"],
            user_id=updated_booking["user_id"],
            room_id=updated_booking["room_id"],
            check_in_date=updated_booking["check_in_date"],
            check_out_date=updated_booking["check_out_date"],
            status=updated_booking["status"],
            payment_status=updated_booking["payment_status"],
            total_price=updated_booking["total_price"],
            special_requests=updated_booking.get("special_requests"),
            created_at=updated_booking["created_at"],
            updated_at=updated_booking["updated_at"],
            transaction_id=updated_booking.get("transaction_id")
        )

    @strawberry.mutation
    async def check_out_booking(self, info, id: int) -> Optional[BookingType]:
        # Get booking
        booking = await Booking.get_by_id(id)
        if not booking:
            return None
        
        # Check booking status
        if booking["status"] != BookingStatus.CHECKED_IN.value:
            return None
        
        # Update booking status
        updated_booking = await Booking.update_status(
            id,
            BookingStatus.CHECKED_OUT.value
        )
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=updated_booking["id"],
            user_id=updated_booking["user_id"],
            room_id=updated_booking["room_id"],
            check_in_date=updated_booking["check_in_date"],
            check_out_date=updated_booking["check_out_date"],
            status=updated_booking["status"],
            payment_status=updated_booking["payment_status"],
            total_price=updated_booking["total_price"],
            special_requests=updated_booking.get("special_requests"),
            created_at=updated_booking["created_at"],
            updated_at=updated_booking["updated_at"],
            transaction_id=updated_booking.get("transaction_id")
        )

    @strawberry.mutation
    async def cancel_booking(self, info, id: int) -> Optional[BookingType]:
        # Get booking
        booking = await Booking.get_by_id(id)
        if not booking:
            return None
        
        # Cancel booking
        cancelled_booking = await Booking.cancel_booking(id)
        if not cancelled_booking:
            return None
        
        # Convert snake_case to camelCase for GraphQL response
        return BookingType(
            id=cancelled_booking["id"],
            user_id=cancelled_booking["user_id"],
            room_id=cancelled_booking["room_id"],
            check_in_date=cancelled_booking["check_in_date"],
            check_out_date=cancelled_booking["check_out_date"],
            status=cancelled_booking["status"],
            payment_status=cancelled_booking["payment_status"],
            total_price=cancelled_booking["total_price"],
            special_requests=cancelled_booking.get("special_requests"),
            created_at=cancelled_booking["created_at"],
            updated_at=cancelled_booking["updated_at"],
            transaction_id=cancelled_booking.get("transaction_id")
        )

# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)

# GraphQL context dependency
async def get_context(request: Request) -> Dict[str, Any]:
    return {
        "request": request
    }

# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)

# Add GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Add REST endpoints
@app.get("/")
async def root():
    return {"message": "Booking Service with GraphQL API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# No need to initialize database since we're using in-memory storage

if __name__ == "__main__":
    # Run the application
    uvicorn.run("run_app:app", host="0.0.0.0", port=8010, reload=True)
