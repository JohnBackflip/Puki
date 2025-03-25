import pytest
from datetime import datetime, timedelta
from ..models import DigitalKey, SecurityEvent, SecurityEventType

def test_digital_key_creation(mock_cursor):
    # Test data
    key_data = {
        "booking_id": 1,
        "room_id": 101,
        "key_hash": "test_hash",
        "valid_from": datetime.now(),
        "valid_until": datetime.now() + timedelta(days=1),
        "is_active": True
    }
    
    # Create key
    key = DigitalKey.create(mock_cursor, key_data)
    
    # Assertions
    assert key["id"] == 1
    assert key["booking_id"] == key_data["booking_id"]
    assert key["room_id"] == key_data["room_id"]
    assert key["key_hash"] == key_data["key_hash"]
    assert key["is_active"] == key_data["is_active"]

def test_digital_key_retrieval(mock_cursor):
    # Create test key
    key_data = {
        "booking_id": 1,
        "room_id": 101,
        "key_hash": "test_hash",
        "valid_from": datetime.now(),
        "valid_until": datetime.now() + timedelta(days=1),
        "is_active": True
    }
    key = DigitalKey.create(mock_cursor, key_data)
    
    # Test retrieval
    retrieved_key = DigitalKey.get_by_id(mock_cursor, key["id"])
    assert retrieved_key == key

def test_digital_key_status_update(mock_cursor):
    # Create test key
    key_data = {
        "booking_id": 1,
        "room_id": 101,
        "key_hash": "test_hash",
        "valid_from": datetime.now(),
        "valid_until": datetime.now() + timedelta(days=1),
        "is_active": True
    }
    key = DigitalKey.create(mock_cursor, key_data)
    
    # Update status
    updated_key = DigitalKey.update_status(mock_cursor, key["id"], False)
    assert updated_key["is_active"] is False

def test_security_event_creation(mock_cursor):
    # Test data
    event_data = {
        "user_id": 1,
        "type": SecurityEventType.LOGIN.value,
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "details": {"success": True}
    }
    
    # Create event
    event = SecurityEvent.create(mock_cursor, event_data)
    
    # Assertions
    assert event["id"] == 1
    assert event["user_id"] == event_data["user_id"]
    assert event["type"] == event_data["type"]
    assert event["ip_address"] == event_data["ip_address"]
    assert event["user_agent"] == event_data["user_agent"]
    assert event["details"] == event_data["details"]

def test_security_event_retrieval(mock_cursor):
    # Create test event
    event_data = {
        "user_id": 1,
        "type": SecurityEventType.LOGIN.value,
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0",
        "details": {"success": True}
    }
    event = SecurityEvent.create(mock_cursor, event_data)
    
    # Test retrieval
    retrieved_event = SecurityEvent.get_by_id(mock_cursor, event["id"])
    assert retrieved_event == event

def test_security_event_filtering(mock_cursor):
    # Create test events
    events = [
        SecurityEvent.create(mock_cursor, {
            "user_id": 1,
            "type": SecurityEventType.LOGIN.value,
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "details": {"success": True}
        }),
        SecurityEvent.create(mock_cursor, {
            "user_id": 2,
            "type": SecurityEventType.LOGOUT.value,
            "ip_address": "127.0.0.1",
            "user_agent": "Mozilla/5.0",
            "details": {"success": True}
        })
    ]
    
    # Test filtering by user
    user_events = SecurityEvent.get_by_user(mock_cursor, 1)
    assert len(user_events) == 1
    assert user_events[0]["user_id"] == 1
    
    # Test filtering by type
    login_events = SecurityEvent.get_by_type(mock_cursor, SecurityEventType.LOGIN.value)
    assert len(login_events) == 1
    assert login_events[0]["type"] == SecurityEventType.LOGIN.value 