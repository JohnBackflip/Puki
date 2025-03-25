import pytest
from fastapi.testclient import TestClient
from monitoring.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_update_request_count():
    data = {
        "method": "GET",
        "endpoint": "/rooms/",
        "count": 1
    }
    response = client.post("/metrics/request_count", json=data)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_update_room_availability():
    data = {
        "room_type": "DOUBLE",
        "count": 5
    }
    response = client.post("/metrics/room_availability", json=data)
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "room_availability" in response.text 