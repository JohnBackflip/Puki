import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from services.booking.main import app as booking_app
from services.event.main import app as event_app
from services.booking.database import get_db as get_booking_db
from services.event.database import get_db as get_event_db
from services.booking import models as booking_models
from services.event import models as event_models

# Test clients
booking_client = TestClient(booking_app)
event_client = TestClient(event_app)

# Test data
TEST_USER = {
    "username": "testuser",
    "password": "testpass",
    "role": "admin",
    "user_id": 1
}

# Test headers with mock authentication
TEST_HEADERS = {
    "Authorization": "Bearer test_token",
    "X-User-Data": '{"user_id": 1, "username": "testuser", "role": "admin", "scopes": ["admin"]}'
}

TEST_ROOM = {
    "room_number": "101",
    "room_type": "standard",
    "price": 100.0,
    "capacity": 2
}

@pytest.fixture(autouse=True)
def setup_database():
    # Get database connections
    booking_db = get_booking_db()  # No need for next() since it's not a generator anymore
    event_db = get_event_db()
    
    # Create tables in booking database
    with booking_db.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(10) NOT NULL UNIQUE,
                room_type ENUM('standard', 'deluxe', 'suite') NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                capacity INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                room_id INT NOT NULL,
                check_in_date DATE NOT NULL,
                check_out_date DATE NOT NULL,
                status ENUM('pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled') NOT NULL DEFAULT 'pending',
                total_price DECIMAL(10, 2) NOT NULL,
                special_requests TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS booking_payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                transaction_id VARCHAR(100),
                status ENUM('pending', 'paid', 'refunded', 'failed') NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (booking_id) REFERENCES bookings(id)
            )
        """)
    booking_db.commit()
    
    # Create tables in event database
    with event_db.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                event_type VARCHAR(50) NOT NULL,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                location VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_adjustments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                adjustment_type ENUM('percentage', 'fixed') NOT NULL,
                value DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        """)
    event_db.commit()
    
    yield
    
    # Clean up tables
    with booking_db.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS booking_payments")
        cursor.execute("DROP TABLE IF EXISTS bookings")
        cursor.execute("DROP TABLE IF EXISTS rooms")
    booking_db.commit()
    
    with event_db.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS price_adjustments")
        cursor.execute("DROP TABLE IF EXISTS events")
    event_db.commit()
    
    # Close connections
    booking_db.close()
    event_db.close()

def test_event_creation_and_booking_flow():
    """Test the complete flow from event creation to booking with price adjustments"""
    
    # 1. Create an event
    event_data = {
        "name": "Test Conference",
        "description": "Annual tech conference",
        "event_type": "conference",
        "start_date": (datetime.now() + timedelta(days=10)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=12)).isoformat(),
        "location": "Conference Center"
    }
    response = event_client.post("/events", json=event_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    event_id = response.json()["id"]
    
    # 2. Create a price adjustment for the event
    adjustment_data = {
        "event_id": event_id,
        "adjustment_type": "percentage",
        "value": 10.0  # 10% increase
    }
    response = event_client.post("/events/price-adjustments", json=adjustment_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    # 3. Create a room
    response = booking_client.post("/rooms", json=TEST_ROOM, headers=TEST_HEADERS)
    assert response.status_code == 200
    room_id = response.json()["id"]
    
    # 4. Create a booking during the event
    booking_data = {
        "room_id": room_id,
        "check_in_date": (datetime.now() + timedelta(days=10)).date().isoformat(),
        "check_out_date": (datetime.now() + timedelta(days=11)).date().isoformat(),
        "total_price": 110.0,  # Base price + 10% event adjustment
        "special_requests": "Near elevator"
    }
    response = booking_client.post("/bookings", json=booking_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    booking = response.json()
    assert booking["total_price"] == 110.0  # Verify price includes event adjustment

def test_booking_conflicts_with_event():
    """Test that bookings cannot be made during events if the room is fully booked"""
    
    # 1. Create an event
    event_data = {
        "name": "Test Conference",
        "description": "Annual tech conference",
        "event_type": "conference",
        "start_date": (datetime.now() + timedelta(days=20)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=22)).isoformat(),
        "location": "Conference Center"
    }
    response = event_client.post("/events", json=event_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    # 2. Create a room
    response = booking_client.post("/rooms", json=TEST_ROOM, headers=TEST_HEADERS)
    assert response.status_code == 200
    room_id = response.json()["id"]
    
    # 3. Create first booking during the event
    booking_data = {
        "room_id": room_id,
        "check_in_date": (datetime.now() + timedelta(days=20)).date().isoformat(),
        "check_out_date": (datetime.now() + timedelta(days=21)).date().isoformat(),
        "total_price": 100.0,
        "special_requests": "Near elevator"
    }
    response = booking_client.post("/bookings", json=booking_data, headers=TEST_HEADERS)
    assert response.status_code == 200
    
    # 4. Try to create second booking for the same dates
    response = booking_client.post("/bookings", json=booking_data, headers=TEST_HEADERS)
    assert response.status_code == 400  # Should fail as room is not available 