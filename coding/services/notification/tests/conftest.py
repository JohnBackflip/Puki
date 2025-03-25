import pytest
from datetime import datetime
from typing import Dict, Any

class MockCursor:
    def __init__(self):
        self.notifications = []
        self.preferences = []
        
    def execute(self, query: str, params: tuple = None):
        if "INSERT INTO notifications" in query:
            notification_id = len(self.notifications) + 1
            self.notifications.append({
                "id": notification_id,
                "user_id": params[0],
                "type": params[1],
                "title": params[2],
                "message": params[3],
                "is_read": params[4],
                "metadata": params[5],
                "created_at": datetime.now()
            })
            self.lastrowid = notification_id
        elif "INSERT INTO notification_preferences" in query:
            pref_id = len(self.preferences) + 1
            self.preferences.append({
                "id": pref_id,
                "user_id": params[0],
                "type": params[1],
                "email_enabled": params[2],
                "push_enabled": params[3],
                "sms_enabled": params[4],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            self.lastrowid = pref_id
        elif "SELECT * FROM notifications" in query:
            if "WHERE id = %s" in query:
                self._last_result = [n for n in self.notifications if n["id"] == params[0]]
            elif "WHERE user_id = %s" in query:
                self._last_result = [n for n in self.notifications if n["user_id"] == params[0]]
            elif "WHERE type = %s" in query:
                self._last_result = [n for n in self.notifications if n["type"] == params[0]]
            else:
                self._last_result = self.notifications
        elif "SELECT * FROM notification_preferences" in query:
            if "WHERE id = %s" in query:
                self._last_result = [p for p in self.preferences if p["id"] == params[0]]
            elif "WHERE user_id = %s" in query:
                self._last_result = [p for p in self.preferences if p["user_id"] == params[0]]
            else:
                self._last_result = self.preferences
        elif "UPDATE notifications" in query:
            for notification in self.notifications:
                if notification["id"] == params[1]:
                    notification["is_read"] = params[0]
                    break
            self.rowcount = 1
        elif "UPDATE notification_preferences" in query:
            for pref in self.preferences:
                if pref["id"] == params[1]:
                    pref["email_enabled"] = params[0]
                    pref["push_enabled"] = params[2]
                    pref["sms_enabled"] = params[3]
                    break
            self.rowcount = 1
        elif "DELETE FROM notifications" in query:
            self.notifications = [n for n in self.notifications if n["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM notification_preferences" in query:
            self.preferences = [p for p in self.preferences if p["id"] != params[0]]
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