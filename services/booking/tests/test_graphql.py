import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import mysql.connector.pooling
from unittest.mock import patch

from services.booking.run_app import app
import services.booking.run_app
from services.booking.database import init_db

# Use the same database instance as the app
from services.booking.run_app import db

@pytest.fixture(autouse=True)
def setup_database(mock_db):
    """Setup a clean database for each test."""
    # Replace the app's db with our mock
    services.booking.run_app.db = mock_db
    yield
    # Restore the original db after the test
    services.booking.run_app.db = db

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

def test_get_bookings(client):
    """Test the bookings query to retrieve all bookings."""
    # Get all bookings
    
    # Now get all bookings
    query = """
    query {
        bookings {
            id
            user_id
            room_id
            check_in_date
            check_out_date
            status
            payment_status
            total_price
            created_at
            updated_at
        }
    }
    """

    response = client.post(
        "/graphql",
        json={"query": query}
    )

    assert response.status_code == 200
    data = response.json()
    print("Response data:", data)
    print("Database state:", db.bookings)
    assert "data" in data
    assert "bookings" in data["data"]
    assert isinstance(data["data"]["bookings"], list)
    assert len(data["data"]["bookings"]) > 0  # Should have sample data
    
    # Verify the structure of a booking
    booking = data["data"]["bookings"][0]
    assert "id" in booking
    assert "user_id" in booking
    assert "room_id" in booking
    assert "check_in_date" in booking
    assert "check_out_date" in booking
    assert "status" in booking

def test_get_booking_by_id(client):
    """Test the booking query to retrieve a specific booking by ID."""
    # Create a booking first
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    checkout = (date.today() + timedelta(days=4)).isoformat()
    create_mutation = f"""
    mutation {{
        createBooking(booking: {{
            user_id: 6,
            room_id: 202,
            check_in_date: "{tomorrow}",
            check_out_date: "{checkout}",
            total_price: 350.00,
            special_requests: "None"
        }}) {{
            id
        }}
    }}
    """
    response = client.post(
        "/graphql",
        json={"query": create_mutation}
    )
    assert response.status_code == 200
    data = response.json()
    booking_id = data["data"]["createBooking"]["id"]

    # Now query for a specific booking
    query = f"""
    query {{
        booking(id: {booking_id}) {{
            id
            user_id
            room_id
            check_in_date
            check_out_date
            status
            payment_status
            total_price
            special_requests
        }}
    }}
    """

    response = client.post(
        "/graphql",
        json={"query": query}
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "booking" in data["data"]
    assert data["data"]["booking"]["id"] == booking_id

def test_create_booking(client):
    """Test the createBooking mutation."""
    # Get tomorrow's date and 3 days after for check-in/check-out
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    checkout = (date.today() + timedelta(days=4)).isoformat()
    
    mutation = f"""
    mutation {{
        createBooking(booking: {{
            user_id: 5,
            room_id: 201,
            check_in_date: "{tomorrow}",
            check_out_date: "{checkout}",
            total_price: 450.00,
            special_requests: "Extra pillows please"
        }}) {{
            id
            user_id
            room_id
            check_in_date
            check_out_date
            status
            payment_status
            total_price
            special_requests
        }}
    }}
    """
    
    response = client.post(
        "/graphql",
        json={"query": mutation}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "createBooking" in data["data"]
    
    booking = data["data"]["createBooking"]
    assert booking["user_id"] == 5
    assert booking["room_id"] == 201
    assert booking["check_in_date"] == tomorrow
    assert booking["check_out_date"] == checkout
    assert booking["status"] == "pending"
    assert booking["total_price"] == 450.0
    assert booking["special_requests"] == "Extra pillows please"

def test_update_booking(client):
    """Test the updateBooking mutation."""
    # First create a booking to update
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    checkout = (date.today() + timedelta(days=4)).isoformat()
    
    create_mutation = f"""
    mutation {{
        createBooking(booking: {{
            user_id: 6,
            room_id: 202,
            check_in_date: "{tomorrow}",
            check_out_date: "{checkout}",
            total_price: 350.00,
            special_requests: "None"
        }}) {{
            id
        }}
    }}
    """
    
    response = client.post(
        "/graphql",
        json={"query": create_mutation}
    )
    
    data = response.json()
    booking_id = data["data"]["createBooking"]["id"]
    
    # New checkout date (extend by 2 days)
    new_checkout = (date.today() + timedelta(days=6)).isoformat()
    
    # Update the booking
    update_mutation = f"""
    mutation {{
        updateBooking(
            id: {booking_id}, 
            booking: {{
                check_out_date: "{new_checkout}",
                special_requests: "Late checkout requested"
            }}
        ) {{
            id
            check_out_date
            special_requests
        }}
    }}
    """
    
    response = client.post(
        "/graphql",
        json={"query": update_mutation}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "updateBooking" in data["data"]
    
    updated = data["data"]["updateBooking"]
    assert updated["id"] == booking_id
    assert updated["check_out_date"] == new_checkout
    assert updated["special_requests"] == "Late checkout requested"

def test_cancel_booking(client):
    """Test the cancelBooking mutation."""
    # First create a booking to cancel
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    checkout = (date.today() + timedelta(days=4)).isoformat()
    
    create_mutation = f"""
    mutation {{
        createBooking(booking: {{
            user_id: 7,
            room_id: 203,
            check_in_date: "{tomorrow}",
            check_out_date: "{checkout}",
            total_price: 550.00,
            special_requests: "None"
        }}) {{
            id
        }}
    }}
    """
    
    response = client.post(
        "/graphql",
        json={"query": create_mutation}
    )
    
    data = response.json()
    booking_id = data["data"]["createBooking"]["id"]
    
    # Cancel the booking
    cancel_mutation = f"""
    mutation {{
        cancelBooking(id: {booking_id}) {{
            id
            status
        }}
    }}
    """
    
    response = client.post(
        "/graphql",
        json={"query": cancel_mutation}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "cancelBooking" in data["data"]
    
    cancelled = data["data"]["cancelBooking"]
    assert cancelled["id"] == booking_id
    assert cancelled["status"] == "cancelled"
