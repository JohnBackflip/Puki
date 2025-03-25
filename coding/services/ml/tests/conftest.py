import pytest
from datetime import datetime
from typing import Dict, Any

class MockCursor:
    def __init__(self):
        self.predictions = []
        self.training_data = []
        self.model_versions = []
        
    def execute(self, query: str, params: tuple = None):
        if "INSERT INTO predictions" in query:
            prediction_id = len(self.predictions) + 1
            self.predictions.append({
                "id": prediction_id,
                "model_version": params[0],
                "input_data": params[1],
                "prediction": params[2],
                "confidence": params[3],
                "created_at": datetime.now()
            })
            self.lastrowid = prediction_id
        elif "INSERT INTO training_data" in query:
            data_id = len(self.training_data) + 1
            self.training_data.append({
                "id": data_id,
                "input_data": params[0],
                "target_data": params[1],
                "created_at": datetime.now()
            })
            self.lastrowid = data_id
        elif "INSERT INTO model_versions" in query:
            version_id = len(self.model_versions) + 1
            self.model_versions.append({
                "id": version_id,
                "version": params[0],
                "model_path": params[1],
                "metrics": params[2],
                "created_at": datetime.now()
            })
            self.lastrowid = version_id
        elif "SELECT * FROM predictions" in query:
            if "WHERE id = %s" in query:
                self._last_result = [p for p in self.predictions if p["id"] == params[0]]
            elif "WHERE model_version = %s" in query:
                self._last_result = [p for p in self.predictions if p["model_version"] == params[0]]
            else:
                self._last_result = self.predictions
        elif "SELECT * FROM training_data" in query:
            if "WHERE id = %s" in query:
                self._last_result = [d for d in self.training_data if d["id"] == params[0]]
            else:
                self._last_result = self.training_data
        elif "SELECT * FROM model_versions" in query:
            if "WHERE id = %s" in query:
                self._last_result = [v for v in self.model_versions if v["id"] == params[0]]
            elif "WHERE version = %s" in query:
                self._last_result = [v for v in self.model_versions if v["version"] == params[0]]
            else:
                self._last_result = self.model_versions
        elif "DELETE FROM predictions" in query:
            self.predictions = [p for p in self.predictions if p["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM training_data" in query:
            self.training_data = [d for d in self.training_data if d["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM model_versions" in query:
            self.model_versions = [v for v in self.model_versions if v["id"] != params[0]]
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