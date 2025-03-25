import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

class MockCursor:
    def __init__(self):
        self.digital_keys = []
        self.security_events = []
        
    def execute(self, query: str, params: tuple = None):
        if "INSERT INTO digital_keys" in query:
            key_id = len(self.digital_keys) + 1
            self.digital_keys.append({
                "id": key_id,
                "booking_id": params[0],
                "room_id": params[1],
                "key_hash": params[2],
                "valid_from": params[3],
                "valid_until": params[4],
                "is_active": params[5],
                "created_at": datetime.now()
            })
            self.lastrowid = key_id
        elif "INSERT INTO security_events" in query:
            event_id = len(self.security_events) + 1
            self.security_events.append({
                "id": event_id,
                "user_id": params[0],
                "type": params[1],
                "ip_address": params[2],
                "user_agent": params[3],
                "details": params[4],
                "created_at": datetime.now()
            })
            self.lastrowid = event_id
        elif "SELECT * FROM digital_keys" in query:
            if "WHERE id = %s" in query:
                self._last_result = [k for k in self.digital_keys if k["id"] == params[0]]
            elif "WHERE booking_id = %s" in query:
                self._last_result = [k for k in self.digital_keys if k["booking_id"] == params[0]]
            elif "WHERE room_id = %s" in query:
                self._last_result = [k for k in self.digital_keys if k["room_id"] == params[0]]
            else:
                self._last_result = self.digital_keys
        elif "SELECT * FROM security_events" in query:
            if "WHERE id = %s" in query:
                self._last_result = [e for e in self.security_events if e["id"] == params[0]]
            elif "WHERE user_id = %s" in query:
                self._last_result = [e for e in self.security_events if e["user_id"] == params[0]]
            elif "WHERE type = %s" in query:
                self._last_result = [e for e in self.security_events if e["type"] == params[0]]
            else:
                self._last_result = self.security_events
        elif "UPDATE digital_keys" in query:
            for key in self.digital_keys:
                if key["id"] == params[1]:
                    key["is_active"] = params[0]
                    break
            self.rowcount = 1
        elif "DELETE FROM digital_keys" in query:
            self.digital_keys = [k for k in self.digital_keys if k["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM security_events" in query:
            self.security_events = [e for e in self.security_events if e["id"] != params[0]]
            self.rowcount = 1
    
    def fetchone(self):
        if hasattr(self, '_last_result'):
            return self._last_result[0] if self._last_result else None
        return None
    
    def fetchall(self):
        if hasattr(self, '_last_result'):
            return self._last_result
        return []

@pytest.fixture
def mock_cursor():
    return MockCursor()

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_auth():
    return {
        "user_id": 1,
        "roles": ["user"]
    }

@pytest.fixture
def mock_rabbitmq():
    return {
        "exchange": "test_exchange",
        "routing_key": "test_routing_key",
        "message": {"test": "data"}
    } 