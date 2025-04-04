import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import sys

# Set environment variables for test databases
os.environ["DATABASE_URL"] = "mysql+pymysql://root:root@localhost:3306/test_booking"
os.environ["GUEST_URL"] = "http://localhost:5011"
os.environ["PRICE_URL"] = "http://localhost:8000"

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the models
from booking import Booking, db as booking_db, app as booking_app
from guest import Guest, db as guest_db, app as guest_app
from room import Room, db as room_db, app as room_app
from price import Price, db as price_db, app as price_app

@pytest.fixture(scope="session")
def test_app():
    # Configure test database URLs
    booking_app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost:3306/test_booking"
    booking_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    booking_app.config["TESTING"] = True

    guest_app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost:3306/test_guest"
    guest_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    guest_app.config["TESTING"] = True

    room_app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost:3306/test_room"
    room_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    room_app.config["TESTING"] = True

    price_app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:root@localhost:3306/test_price"
    price_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    price_app.config["TESTING"] = True

    # Create test databases
    with booking_app.app_context():
        booking_db.create_all()
    
    with guest_app.app_context():
        guest_db.create_all()
    
    with room_app.app_context():
        room_db.create_all()
    
    with price_app.app_context():
        price_db.create_all()

    yield booking_app

    # Clean up
    with booking_app.app_context():
        booking_db.drop_all()
    
    with guest_app.app_context():
        guest_db.drop_all()
    
    with room_app.app_context():
        room_db.drop_all()
    
    with price_app.app_context():
        price_db.drop_all()

@pytest.fixture(scope="function")
def client(test_app):
    return test_app.test_client()

@pytest.fixture(scope="function")
def db_session(test_app):
    with test_app.app_context():
        yield booking_db.session
        booking_db.session.rollback() 