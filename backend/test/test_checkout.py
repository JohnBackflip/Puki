import pytest
from flask import json
from checkout import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json["status"] == "healthy"

def test_checkout_success(monkeypatch, client):  
    # Mock RabbitMQ connection and channel
    class DummyChannel:
        def basic_publish(self, exchange, routing_key, body):
            assert "sms_queue" == routing_key
            assert "feedback" in body

        def close(self): pass

    class DummyConnection:
        def close(self): pass

    monkeypatch.setattr("checkout.get_rabbitmq_channel", lambda: (DummyChannel(), DummyConnection()))

    res = client.post("/checkout", json={
        "room_id": "R202",
        "guest_id": 1,
        "mobile_number": "91234567"
    })

    assert res.status_code == 200
    assert res.json["message"] == "Check-out successful!"
