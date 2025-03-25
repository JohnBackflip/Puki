import pytest
from unittest.mock import patch, MagicMock
from typing import Generator
import sys
from pathlib import Path
from functools import wraps
from datetime import datetime
import json
import os

# Add services directory to path
root_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(root_dir)

def load_test_data(service: str, filename: str) -> dict:
    """Load test data from JSON files."""
    data_path = os.path.join(os.path.dirname(__file__), "data", service, filename)
    with open(data_path) as f:
        return json.load(f)

class MockCursor:
    def __init__(self):
        self.rooms = []
        self.availability = []
        self.last_id = 0
        self.last_query = None
        self.last_params = None

    @property
    def lastrowid(self):
        return self.last_id

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        if "INSERT INTO rooms" in query:
            self.last_id += 1
            room = {
                "id": self.last_id,
                "room_number": params[0],
                "room_type": params[1],
                "price_per_night": str(params[2]),
                "floor": params[3],
                "status": "available",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.rooms.append(room)
        elif "UPDATE rooms" in query:
            if "status" in query:
                room_id = params[1]
                new_status = params[0]
                for room in self.rooms:
                    if room["id"] == room_id:
                        room["status"] = new_status
                        room["updated_at"] = datetime.now()
                        break

    def fetchone(self):
        if "LAST_INSERT_ID()" in self.last_query:
            return {"LAST_INSERT_ID()": self.last_id}
        elif "SELECT * FROM rooms WHERE id = %s" in self.last_query:
            room_id = self.last_params[0]
            for room in self.rooms:
                if room["id"] == room_id:
                    return room
            return None
        elif "SELECT * FROM rooms WHERE room_number = %s" in self.last_query:
            room_number = self.last_params[0]
            for room in self.rooms:
                if room["room_number"] == room_number:
                    return room
            return None
        elif "SELECT * FROM room_availability" in self.last_query:
            if self.availability:
                availability = self.availability[0].copy()
                availability["base_price"] = str(availability["base_price"])
                return availability
            return None
        elif "SELECT COUNT(*) as count FROM room_availability" in self.last_query:
            return {"count": 0}
        elif self.rooms:
            return self.rooms[-1]
        return None

    def fetchall(self):
        if "SELECT * FROM rooms" in self.last_query:
            return self.rooms
        elif "SELECT room_type, COUNT(*) as available_count" in self.last_query:
            return [{
                "room_type": "double",
                "available_count": 5,
                "base_price": "200.00"
            }]
        elif "SELECT * FROM room_availability" in self.last_query:
            if self.availability:
                availabilities = []
                for availability in self.availability:
                    availability_copy = availability.copy()
                    availability_copy["base_price"] = str(availability_copy["base_price"])
                    availabilities.append(availability_copy)
                return availabilities
            return [{
                "date": "2025-03-24",
                "room_type": "double",
                "available_count": 5,
                "base_price": "200.00"
            }]
        return self.rooms

    def close(self):
        pass

# Create a single instance of MockCursor to be used across tests
mock_cursor_instance = MockCursor()

@pytest.fixture
def mock_cursor():
    """Return the shared mock cursor instance."""
    return mock_cursor_instance

@pytest.fixture(autouse=True)
def reset_mock_cursor():
    """Reset the mock cursor before each test."""
    mock_cursor_instance.rooms = []
    mock_cursor_instance.availability = []
    mock_cursor_instance.last_id = 0
    mock_cursor_instance.last_query = None
    mock_cursor_instance.last_params = None
    return mock_cursor_instance

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_auth():
    return {"user_id": 1, "token": "test_token", "roles": ["admin"]}

# Mock RabbitMQ
class MockExchange:
    async def publish(self, message, routing_key):
        pass

class MockChannel:
    async def declare_exchange(self, name, type=None):
        return MockExchange()

    async def get_exchange(self, name):
        return MockExchange()

class MockConnection:
    def __init__(self):
        self.is_closed = False
        self._channel = MockChannel()

    async def channel(self):
        return self._channel

    async def close(self):
        self.is_closed = True

@pytest.fixture
async def mock_rabbitmq():
    return MockConnection()

# Service-specific fixtures
@pytest.fixture
def room_test_data():
    """Load room test data."""
    return load_test_data("room", "rooms.json")

@pytest.fixture
def room_availability_test_data():
    """Load room availability test data."""
    return load_test_data("room", "availability.json") 