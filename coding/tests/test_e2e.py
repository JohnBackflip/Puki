import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from api_gateway.main import app
from services.booking.database import engine as booking_engine
from services.event.database import engine as event_engine
from services.booking import models as booking_models
from services.event import models as event_models

# Test client
client = TestClient(app)

# Test data
TEST_USER = {
    "username": "testuser",
    "password": "testpass",
    "role": "admin"
}

TEST_ROOM = {
    "room_number": "101",
    "room_type": "standard",
    "price": 100.0,
    "capacity": 2
}

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    booking_models.Base.metadata.create_all(bind=booking_engine)
    event_models.Base.metadata.create_all(bind=event_engine)
    
    yield
    
    # Clean up tables
    booking_models.Base.metadata.drop_all(bind=booking_engine)
    event_models.Base.metadata.drop_all(bind=event_engine)

def test_complete_booking_flow():
    """Test the complete booking flow through the API gateway"""
    
    # 1. Create an event
    event_data = {
        "name": "Test Conference",
        "description": "Annual tech conference",
        "event_type": "conference",
        "start_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=12)).isoformat(),
        "location": "Convention Center",
        "expected_attendance": 100
    }
    
    event_response = client.post(
        "/api/events/",
        json=event_data,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert event_response.status_code == 200
    event_id = event_response.json()["id"]
    
    # 2. Create a price adjustment
    adjustment_data = {
        "event_id": event_id,
        "room_type": "standard",
        "adjustment_type": "percentage",
        "adjustment_value": 10.0,
        "valid_from": (datetime.now() + timedelta(days=10)).isoformat(),
        "valid_until": (datetime.now() + timedelta(days=12)).isoformat()
    }
    
    adjustment_response = client.post(
        "/api/price-adjustments/",
        json=adjustment_data,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert adjustment_response.status_code == 200
    
    # 3. Create a room
    room_response = client.post(
        "/api/rooms/",
        json=TEST_ROOM,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert room_response.status_code == 200
    room_id = room_response.json()["id"]
    
    # 4. Check room availability
    availability_response = client.get(
        f"/api/rooms/{room_id}/availability",
        params={
            "check_in_date": (datetime.now() + timedelta(days=10)).isoformat(),
            "check_out_date": (datetime.now() + timedelta(days=12)).isoformat()
        },
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert availability_response.status_code == 200
    assert availability_response.json()["available"] is True
    
    # 5. Calculate price
    price_response = client.post(
        "/api/calculate-price/",
        json={
            "room_type": "standard",
            "check_in_date": (datetime.now() + timedelta(days=10)).isoformat(),
            "check_out_date": (datetime.now() + timedelta(days=12)).isoformat(),
            "base_price": 100.0
        },
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert price_response.status_code == 200
    price_data = price_response.json()
    assert price_data["original_price"] == 200.0
    assert price_data["adjusted_price"] == 220.0
    
    # 6. Create a booking
    booking_data = {
        "room_id": room_id,
        "guest_name": "John Doe",
        "check_in_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "check_out_date": (datetime.now() + timedelta(days=12)).isoformat(),
        "number_of_guests": 2
    }
    
    booking_response = client.post(
        "/api/bookings/",
        json=booking_data,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]
    
    # 7. Verify booking details
    booking_details_response = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert booking_details_response.status_code == 200
    booking_details = booking_details_response.json()
    assert booking_details["guest_name"] == "John Doe"
    assert booking_details["number_of_guests"] == 2
    assert booking_details["status"] == "confirmed"
    
    # 8. Cancel booking
    cancel_response = client.post(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert cancel_response.status_code == 200
    
    # 9. Verify booking is cancelled
    cancelled_booking_response = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert cancelled_booking_response.status_code == 200
    assert cancelled_booking_response.json()["status"] == "cancelled"

def test_error_handling():
    """Test error handling through the API gateway"""
    
    # Test invalid event creation
    invalid_event_data = {
        "name": "",  # Empty name
        "description": "Test event",
        "event_type": "conference",
        "start_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=12)).isoformat(),
        "location": "Test Location",
        "expected_attendance": 100
    }
    
    response = client.post(
        "/api/events/",
        json=invalid_event_data,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert response.status_code == 422
    
    # Test invalid booking dates
    invalid_booking_data = {
        "room_id": 1,
        "guest_name": "John Doe",
        "check_in_date": (datetime.now() + timedelta(days=12)).isoformat(),
        "check_out_date": (datetime.now() + timedelta(days=10)).isoformat(),  # Check-out before check-in
        "number_of_guests": 2
    }
    
    response = client.post(
        "/api/bookings/",
        json=invalid_booking_data,
        headers={"Authorization": f"Bearer {TEST_USER['username']}"}
    )
    assert response.status_code == 400
    
    # Test unauthorized access
    response = client.get("/api/events/")
    assert response.status_code == 401 