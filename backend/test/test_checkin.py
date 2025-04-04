import pytest
from flask import json
from checkin import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json["status"] == "healthy"

def test_self_checkin_success(monkeypatch, client):
    today = "2025-04-10"

    # Mock /bookings/<id>
    monkeypatch.setattr("requests.get", lambda url: type("Response", (object,), {
        "status_code": 200,
        "json": lambda: {
            "data": {
                "guest_id": 1,
                "room_id": "R101",
                "check_in": today
            }
        }
    })() if "bookings" in url else
    type("Response", (object,), {
        "status_code": 200,
        "json": lambda: {
            "data": {
                "name": "John Doe"
            }
        }
    })())

    # Mock keycard POST
    monkeypatch.setattr("requests.post", lambda url, json: type("Response", (object,), {
        "status_code": 201,
        "json": lambda: {
            "data": {
                "pin": "1234",
                "room_id": json["room_id"]
            }
        }
    })())

    res = client.post("/self-checkin", json={
        "booking_id": 1,
        "full_name": "John Doe"
    })

    assert res.status_code == 200
    assert "keycard" in res.json
    assert res.json["keycard"]["pin"] == "1234"
