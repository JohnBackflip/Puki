import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from security.main import app
from security.models import KeycardStatus
from security.database import get_db
from sqlalchemy.orm import Session

client = TestClient(app)

def test_digital_keycard_creation_and_activation():
    """Test creating and activating a digital keycard"""
    # Create a test booking
    tomorrow = datetime.now() + timedelta(days=1)
    checkout = tomorrow + timedelta(days=3)
    
    booking_response = client.post(
        "/bookings/",
        json={
            "user_id": 1,
            "room_id": 101,
            "check_in_date": tomorrow.isoformat(),
            "check_out_date": checkout.isoformat(),
            "total_price": 300.00,
            "special_requests": "None"
        }
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]
    
    # Create a digital keycard
    keycard_response = client.post(
        "/keycards/",
        json={
            "booking_id": booking_id,
            "room_id": 101,
            "valid_from": tomorrow.isoformat(),
            "valid_until": checkout.isoformat()
        }
    )
    assert keycard_response.status_code == 200
    keycard_id = keycard_response.json()["id"]
    
    # Verify keycard details
    keycard_data = keycard_response.json()
    assert keycard_data["status"] == KeycardStatus.ACTIVE.value
    assert keycard_data["booking_id"] == booking_id
    assert keycard_data["room_id"] == 101
    assert "digital_key" in keycard_data
    
    # Test keycard validation
    validation_response = client.post(
        f"/keycards/{keycard_id}/validate",
        json={
            "digital_key": keycard_data["digital_key"],
            "room_id": 101
        }
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["is_valid"] == True

def test_keycard_deactivation():
    """Test deactivating a digital keycard"""
    # Create a test booking
    tomorrow = datetime.now() + timedelta(days=1)
    checkout = tomorrow + timedelta(days=3)
    
    booking_response = client.post(
        "/bookings/",
        json={
            "user_id": 1,
            "room_id": 102,
            "check_in_date": tomorrow.isoformat(),
            "check_out_date": checkout.isoformat(),
            "total_price": 300.00,
            "special_requests": "None"
        }
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]
    
    # Create a digital keycard
    keycard_response = client.post(
        "/keycards/",
        json={
            "booking_id": booking_id,
            "room_id": 102,
            "valid_from": tomorrow.isoformat(),
            "valid_until": checkout.isoformat()
        }
    )
    assert keycard_response.status_code == 200
    keycard_id = keycard_response.json()["id"]
    
    # Deactivate the keycard
    deactivate_response = client.post(f"/keycards/{keycard_id}/deactivate")
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["status"] == KeycardStatus.DEACTIVATED.value
    
    # Verify keycard is no longer valid
    validation_response = client.post(
        f"/keycards/{keycard_id}/validate",
        json={
            "digital_key": keycard_response.json()["digital_key"],
            "room_id": 102
        }
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["is_valid"] == False

def test_keycard_expiration():
    """Test keycard expiration"""
    # Create a test booking with a very short duration
    now = datetime.now()
    short_checkout = now + timedelta(minutes=5)
    
    booking_response = client.post(
        "/bookings/",
        json={
            "user_id": 1,
            "room_id": 103,
            "check_in_date": now.isoformat(),
            "check_out_date": short_checkout.isoformat(),
            "total_price": 100.00,
            "special_requests": "None"
        }
    )
    assert booking_response.status_code == 200
    booking_id = booking_response.json()["id"]
    
    # Create a digital keycard
    keycard_response = client.post(
        "/keycards/",
        json={
            "booking_id": booking_id,
            "room_id": 103,
            "valid_from": now.isoformat(),
            "valid_until": short_checkout.isoformat()
        }
    )
    assert keycard_response.status_code == 200
    keycard_id = keycard_response.json()["id"]
    
    # Wait for keycard to expire (simulated)
    import time
    time.sleep(6 * 60)  # Wait 6 minutes
    
    # Verify keycard is expired
    validation_response = client.post(
        f"/keycards/{keycard_id}/validate",
        json={
            "digital_key": keycard_response.json()["digital_key"],
            "room_id": 103
        }
    )
    assert validation_response.status_code == 200
    assert validation_response.json()["is_valid"] == False
    assert validation_response.json()["status"] == KeycardStatus.EXPIRED.value 