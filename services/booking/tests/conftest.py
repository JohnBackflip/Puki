import pytest
from datetime import datetime, date
from typing import Dict, Any
from unittest.mock import MagicMock

class MockDB:
    def __init__(self):
        self.bookings = {}
        self.booking_counter = 1
        
    def _add_sample_data(self):
        self.bookings[1] = {
            "id": 1,
            "user_id": 1,
            "room_id": 101,
            "check_in_date": date(2024, 3, 1),
            "check_out_date": date(2024, 3, 3),
            "status": "confirmed",
            "payment_status": "paid",
            "total_price": 300.00,
            "special_requests": "None",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

@pytest.fixture
def mock_db():
    db = MockDB()
    db._add_sample_data()
    return db

@pytest.fixture
def mock_mysql_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn

@pytest.fixture
def mock_mysql_pool():
    mock_pool = MagicMock()
    mock_pool.get_connection.return_value = mock_mysql_connection()
    return mock_pool

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_auth():
    return {
        "user_id": 1,
        "roles": ["admin"]
    }

@pytest.fixture
def mock_rabbitmq():
    return {
        "exchange": "test_exchange",
        "routing_key": "test_routing_key",
        "message": {"test": "data"}
    } 