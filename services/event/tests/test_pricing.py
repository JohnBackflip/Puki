import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
from services.event.main import app
from services.event.models import EventType, PriceAdjustmentType
from services.event.database import get_db
from sqlalchemy.orm import Session

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = mock_db
    yield
    app.dependency_overrides = {}

def test_event_creation_and_price_adjustment():
    """Test creating an event and its associated price adjustments"""
    # Create a test event
    tomorrow = datetime.now(ZoneInfo("UTC")) + timedelta(days=1)
    next_week = tomorrow + timedelta(days=7)
    
    event_response = client.post(
        "/events/",
        json={
            "name": "Test Conference",
            "description": "A test conference event",
            "event_type": EventType.CONFERENCE.value,
            "start_date": tomorrow.isoformat(),
            "end_date": next_week.isoformat(),
            "location": "Test Location",
            "expected_attendance": 100
        },
        headers={"Authorization": "Bearer test_token"}
    )
    print("Event response:", event_response.json())
    assert event_response.status_code == 200
    event_id = event_response.json()["id"]
    
    # Create a price adjustment for the event
    adjustment_response = client.post(
        "/price-adjustments/",
        json={
            "event_id": event_id,
            "room_type": "standard",
            "adjustment_type": PriceAdjustmentType.PERCENTAGE.value,
            "adjustment_value": 20.0,  # 20% increase
            "valid_from": tomorrow.isoformat(),
            "valid_until": next_week.isoformat()
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert adjustment_response.status_code == 200
    adjustment_id = adjustment_response.json()["id"]
    
    # Test price calculation
    check_in = tomorrow + timedelta(days=2)
    check_out = check_in + timedelta(days=3)
    
    price_response = client.post(
        "/calculate-price/",
        json={
            "room_type": "standard",
            "base_price": 100.0,
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat()
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert price_response.status_code == 200
    price_data = price_response.json()
    
    # Verify price calculation
    # Original price: 100 * 3 = 300
    # With 20% increase: 300 * 1.2 = 360
    assert price_data["original_price"] == 300.0
    assert price_data["adjusted_price"] == 360.0
    assert len(price_data["adjustments"]) == 1

def test_multiple_price_adjustments():
    """Test applying multiple price adjustments"""
    # Create a test event
    tomorrow = datetime.now(ZoneInfo("UTC")) + timedelta(days=1)
    next_week = tomorrow + timedelta(days=7)
    
    event_response = client.post(
        "/events/",
        json={
            "name": "Test Festival",
            "description": "A test festival event",
            "event_type": EventType.FESTIVAL.value,
            "start_date": tomorrow.isoformat(),
            "end_date": next_week.isoformat(),
            "location": "Test Location",
            "expected_attendance": 500
        },
        headers={"Authorization": "Bearer test_token"}
    )
    print("Event response:", event_response.json())
    assert event_response.status_code == 200
    event_id = event_response.json()["id"]
    
    # Create multiple price adjustments
    adjustments = [
        {
            "event_id": event_id,
            "room_type": "luxury",
            "adjustment_type": PriceAdjustmentType.PERCENTAGE.value,
            "adjustment_value": 30.0,  # 30% increase
            "valid_from": tomorrow.isoformat(),
            "valid_until": next_week.isoformat()
        },
        {
            "event_id": event_id,
            "room_type": "luxury",
            "adjustment_type": PriceAdjustmentType.FIXED.value,
            "adjustment_value": 50.0,  # $50 per night increase
            "valid_from": tomorrow.isoformat(),
            "valid_until": next_week.isoformat()
        }
    ]
    
    for adjustment in adjustments:
        response = client.post(
            "/price-adjustments/",
            json=adjustment,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
    
    # Test price calculation with multiple adjustments
    check_in = tomorrow + timedelta(days=2)
    check_out = check_in + timedelta(days=3)
    
    price_response = client.post(
        "/calculate-price/",
        json={
            "room_type": "luxury",
            "base_price": 200.0,
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat()
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert price_response.status_code == 200
    price_data = price_response.json()
    
    # Verify price calculation
    # Original price: 200 * 3 = 600
    # With 30% increase: 600 * 1.3 = 780
    # With $50 per night: 780 + (50 * 3) = 930
    assert price_data["original_price"] == 600.0
    assert price_data["adjusted_price"] == 930.0
    assert len(price_data["adjustments"]) == 2 