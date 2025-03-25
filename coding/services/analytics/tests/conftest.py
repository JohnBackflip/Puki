import pytest
from datetime import datetime
from typing import Dict, Any

class MockCursor:
    def __init__(self):
        self.analytics_events = []
        self.analytics_metrics = []
        
    def execute(self, query: str, params: tuple = None):
        if "INSERT INTO analytics_events" in query:
            event_id = len(self.analytics_events) + 1
            self.analytics_events.append({
                "id": event_id,
                "event_type": params[0],
                "user_id": params[1],
                "timestamp": params[2],
                "data": params[3],
                "created_at": datetime.now()
            })
            self.lastrowid = event_id
        elif "INSERT INTO analytics_metrics" in query:
            metric_id = len(self.analytics_metrics) + 1
            self.analytics_metrics.append({
                "id": metric_id,
                "metric_name": params[0],
                "value": params[1],
                "timestamp": params[2],
                "metadata": params[3],
                "created_at": datetime.now()
            })
            self.lastrowid = metric_id
        elif "SELECT * FROM analytics_events" in query:
            if "WHERE id = %s" in query:
                self._last_result = [e for e in self.analytics_events if e["id"] == params[0]]
            elif "WHERE event_type = %s" in query:
                self._last_result = [e for e in self.analytics_events if e["event_type"] == params[0]]
            elif "WHERE user_id = %s" in query:
                self._last_result = [e for e in self.analytics_events if e["user_id"] == params[0]]
            else:
                self._last_result = self.analytics_events
        elif "SELECT * FROM analytics_metrics" in query:
            if "WHERE id = %s" in query:
                self._last_result = [m for m in self.analytics_metrics if m["id"] == params[0]]
            elif "WHERE metric_name = %s" in query:
                self._last_result = [m for m in self.analytics_metrics if m["metric_name"] == params[0]]
            else:
                self._last_result = self.analytics_metrics
        elif "DELETE FROM analytics_events" in query:
            self.analytics_events = [e for e in self.analytics_events if e["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM analytics_metrics" in query:
            self.analytics_metrics = [m for m in self.analytics_metrics if m["id"] != params[0]]
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
        "roles": ["admin"]
    }

@pytest.fixture
def mock_rabbitmq():
    return {
        "exchange": "test_exchange",
        "routing_key": "test_routing_key",
        "message": {"test": "data"}
    } 