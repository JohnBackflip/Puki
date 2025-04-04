import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import patch
from booking import Booking

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:root@localhost:3306/puki"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

@patch("requests.get")
def test_create_booking(mock_get, client, db_session):
    # Mock guest service response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"id": 1, "name": "Test Guest"}

    # Create test data
    check_in = datetime.now().date()
    check_out = check_in + timedelta(days=2)
    booking_data = {
        "guest_id": 1,
        "room_id": "101",
        "check_in": str(check_in),
        "check_out": str(check_out),
        "room_type": "Single",
        "price": 100.0
    }

    # Test successful booking creation
    response = client.post("/bookings", json=booking_data)
    assert response.status_code == 201
    data = response.json["data"]
    assert data["guest_id"] == booking_data["guest_id"]
    assert data["room_id"] == booking_data["room_id"]
    assert data["room_type"] == booking_data["room_type"]
    assert data["price"] == booking_data["price"]

    # Test booking conflict
    response = client.post("/bookings", json=booking_data)
    assert response.status_code == 400
    assert "already booked" in response.json["message"]

    # Test invalid guest
    mock_get.return_value.status_code = 404
    response = client.post("/bookings", json=booking_data)
    assert response.status_code == 400
    assert "Invalid guest_id" in response.json["message"]

def test_get_all_bookings(client, db_session):
    # Create test booking
    booking = Booking(
        guest_id=1,
        room_id="101",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking)
    db_session.commit()

    # Test getting all bookings
    response = client.get("/bookings")
    assert response.status_code == 200
    assert len(response.json["data"]["bookings"]) == 1

def test_get_booking(client, db_session):
    # Create test booking
    booking = Booking(
        guest_id=1,
        room_id="101",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking)
    db_session.commit()

    # Test getting existing booking
    response = client.get(f"/bookings/{booking.booking_id}")
    assert response.status_code == 200
    assert response.json["data"]["booking_id"] == booking.booking_id

    # Test getting non-existent booking
    response = client.get("/bookings/999")
    assert response.status_code == 404

@patch("requests.get")
def test_update_booking(mock_get, client, db_session):
    # Mock guest service response
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"id": 1, "name": "Test Guest"}

    # Create test booking
    booking = Booking(
        guest_id=1,
        room_id="101",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking)
    db_session.commit()

    # Test successful update
    update_data = {
        "room_id": "102",
        "check_in": str(booking.check_in + timedelta(days=1)),
        "check_out": str(booking.check_out + timedelta(days=1)),
        "room_type": "Family",
        "price": 150.0
    }
    response = client.put(f"/bookings/{booking.booking_id}", json=update_data)
    assert response.status_code == 200
    assert response.json["data"]["room_id"] == update_data["room_id"]
    assert response.json["data"]["room_type"] == update_data["room_type"]
    assert response.json["data"]["price"] == update_data["price"]

    # Test update with conflict
    booking2 = Booking(
        guest_id=2,
        room_id="102",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking2)
    db_session.commit()

    response = client.put(f"/bookings/{booking.booking_id}", json=update_data)
    assert response.status_code == 400
    assert "already booked" in response.json["message"]

def test_cancel_booking(client, db_session):
    # Create test booking
    booking = Booking(
        guest_id=1,
        room_id="101",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking)
    db_session.commit()

    # Test successful cancellation
    response = client.delete(f"/bookings/{booking.booking_id}")
    assert response.status_code == 200

    # Test cancelling non-existent booking
    response = client.delete("/bookings/999")
    assert response.status_code == 404

def test_get_active_booking(client, db_session):
    # Create test booking
    booking = Booking(
        guest_id=1,
        room_id="101",
        check_in=datetime.now().date(),
        check_out=datetime.now().date() + timedelta(days=2),
        room_type="Single",
        price=100.0
    )
    db_session.add(booking)
    db_session.commit()

    # Test getting active booking
    response = client.get(f"/bookings/active/{booking.room_id}")
    assert response.status_code == 200
    assert response.json["data"]["booking_id"] == booking.booking_id

    # Test getting active booking for non-existent room
    response = client.get("/bookings/active/999")
    assert response.status_code == 404
