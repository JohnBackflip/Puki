"""
GraphQL schema for the booking service.
"""
import strawberry
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import models

# GraphQL types
@strawberry.type
class BookingStatus:
    value: str

@strawberry.type
class PaymentStatus:
    value: str

@strawberry.type
class BookingPayment:
    id: int
    booking_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Booking:
    id: int
    user_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    status: str
    payment_status: Optional[str]
    total_price: float
    special_requests: Optional[str]
    created_at: datetime
    updated_at: datetime
    transaction_id: Optional[str] = None

# Input types
@strawberry.input
class BookingCreateInput:
    user_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    total_price: float
    special_requests: Optional[str] = None

@strawberry.input
class BookingUpdateInput:
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    special_requests: Optional[str] = None

# Queries
@strawberry.type
class Query:
    @strawberry.field
    async def booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        booking_data = await models.Booking.get_by_id(cursor, id)
        if not booking_data:
            return None
        return Booking(**booking_data)

    @strawberry.field
    async def bookings(
        self, 
        info, 
        user_id: Optional[int] = None, 
        status: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Booking]:
        cursor = info.context["db"]
        
        # Build query
        query_parts = []
        params = []
        
        if user_id:
            query_parts.append("b.user_id = %s")
            params.append(user_id)
        
        if status:
            query_parts.append("b.status = %s")
            params.append(status)
        
        # Construct final query
        query = """
            SELECT b.*, p.status as payment_status, p.transaction_id
            FROM bookings b
            LEFT JOIN booking_payments p ON b.id = p.booking_id
        """
        
        if query_parts:
            query += f" WHERE {' AND '.join(query_parts)}"
        
        query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        # Execute query
        cursor.execute(query, tuple(params))
        bookings_data = cursor.fetchall()
        
        return [Booking(**booking) for booking in bookings_data]

# Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_booking(self, info, booking: BookingCreateInput) -> Booking:
        cursor = info.context["db"]
        
        # Convert to Decimal for database
        total_price = Decimal(str(booking.total_price))
        
        # Create booking
        booking_data = await models.Booking.create(
            cursor,
            booking.user_id,
            booking.room_id,
            booking.check_in_date,
            booking.check_out_date,
            total_price,
            booking.special_requests
        )
        
        return Booking(**booking_data)

    @strawberry.mutation
    async def update_booking(self, info, id: int, booking: BookingUpdateInput) -> Optional[Booking]:
        cursor = info.context["db"]
        
        # Check if booking exists
        existing = await models.Booking.get_by_id(cursor, id)
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
            return Booking(**existing)
        
        # Perform update
        await models.Booking.update(cursor, id, updates)
        
        # Get updated booking
        updated = await models.Booking.get_by_id(cursor, id)
        return Booking(**updated)

    @strawberry.mutation
    async def check_in_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        
        # Get booking
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        
        # Check booking status
        if booking["status"] != models.BookingStatus.CONFIRMED.value:
            return None
        
        # Check payment status
        if booking["payment_status"] != models.PaymentStatus.PAID.value:
            return None
        
        # Update booking status
        updated_booking = await models.Booking.update_status(
            cursor,
            id,
            models.BookingStatus.CHECKED_IN
        )
        
        return Booking(**updated_booking)

    @strawberry.mutation
    async def check_out_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        
        # Get booking
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        
        # Check booking status
        if booking["status"] != models.BookingStatus.CHECKED_IN.value:
            return None
        
        # Update booking status
        updated_booking = await models.Booking.update_status(
            cursor,
            id,
            models.BookingStatus.CHECKED_OUT
        )
        
        return Booking(**updated_booking)

    @strawberry.mutation
    async def cancel_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        
        # Get booking
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        
        # Cancel booking
        cancelled_booking = await models.Booking.cancel_booking(cursor, id)
        if not cancelled_booking:
            return None
        
        return Booking(**cancelled_booking)

# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
