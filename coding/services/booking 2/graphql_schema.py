
import strawberry
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import requests
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

# Input types (note the added customer_id)
@strawberry.input
class BookingCreateInput:
    user_id: int
    customer_id: int  # New field
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
        query_parts = []
        params = []
        if user_id:
            query_parts.append("b.user_id = %s")
            params.append(user_id)
        if status:
            query_parts.append("b.status = %s")
            params.append(status)
        query = """
            SELECT b.*, p.status as payment_status, p.transaction_id
            FROM bookings b
            LEFT JOIN booking_payments p ON b.id = p.booking_id
        """
        if query_parts:
            query += f" WHERE {' AND '.join(query_parts)}"
        query += " ORDER BY b.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        cursor.execute(query, tuple(params))
        bookings_data = cursor.fetchall()
        return [Booking(**booking) for booking in bookings_data]

# Mutations
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_booking(self, info, booking: BookingCreateInput) -> Booking:
        cursor = info.context["db"]
        
        # Validate dates
        if booking.check_out_date <= booking.check_in_date:
            raise Exception("Check-out date must be later than check-in date.")
        
        # Check room availability
        if not models.Booking.check_availability(cursor, booking.room_id, booking.check_in_date, booking.check_out_date):
            raise Exception("Room is already booked for the selected period.")
        
        # Verify staff user existence
        user_check_url = f"http://localhost:5001/users/{booking.user_id}/exists"
        user_response = requests.get(user_check_url)
        if user_response.status_code != 200:
            raise Exception("Invalid staff user_id. Staff does not exist.")
        
        # Verify customer existence
        customer_check_url = f"http://localhost:5003/customers/{booking.customer_id}"
        customer_response = requests.get(customer_check_url)
        if customer_response.status_code != 200:
            raise Exception("Invalid customer_id. Customer does not exist.")
        
        # Convert total_price to Decimal
        total_price = Decimal(str(booking.total_price))
        
        # Create booking (now includes customer_id)
        booking_data = await models.Booking.create(
            cursor,
            booking.user_id,
            booking.customer_id,
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
        existing = await models.Booking.get_by_id(cursor, id)
        if not existing:
            return None
        updates = {}
        if booking.check_in_date:
            updates["check_in_date"] = booking.check_in_date
        if booking.check_out_date:
            updates["check_out_date"] = booking.check_out_date
        if booking.special_requests is not None:
            updates["special_requests"] = booking.special_requests
        if not updates:
            return Booking(**existing)
        updated = await models.Booking.update(id, updates)
        return Booking(**updated)

    @strawberry.mutation
    async def check_in_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        if booking["status"] != models.BookingStatus.CONFIRMED.value:
            return None
        updated_booking = await models.Booking.update_status(cursor, id, models.BookingStatus.CHECKED_IN)
        return Booking(**updated_booking)

    @strawberry.mutation
    async def check_out_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        if booking["status"] != models.BookingStatus.CHECKED_IN.value:
            return None
        updated_booking = await models.Booking.update_status(cursor, id, models.BookingStatus.CHECKED_OUT)
        return Booking(**updated_booking)

    @strawberry.mutation
    async def cancel_booking(self, info, id: int) -> Optional[Booking]:
        cursor = info.context["db"]
        booking = await models.Booking.get_by_id(cursor, id)
        if not booking:
            return None
        cancelled_booking = await models.Booking.cancel_booking(cursor, id)
        if not cancelled_booking:
            return None
        return Booking(**cancelled_booking)

# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
