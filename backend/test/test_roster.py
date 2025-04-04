
import pytest
from roster import app, db, Roster
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test to create a new roster entry
def test_create_roster(client):
    roster_data = {
        "date": "2025-05-01",
        "floor": 1,
        "room_id": "room001",
        "housekeeper_id": 1,
        "completed": False
    }

    res = client.post("/roster", json=roster_data)
    assert res.status_code == 200
    assert res.json["message"] == "Roster entry created successfully."
    assert res.json["data"]["room_id"] == "room001"

# Test to get roster by date
def test_get_roster_by_date(client):
    date = "2025-05-01"
    res = client.get(f"/roster/{date}")
    assert res.status_code == 200
    assert isinstance(res.json["data"], list)  # Check if the response contains a list

# Test to check invalid date in roster
def test_get_invalid_roster_date(client):
    date = "2025-99-99"  # Invalid date
    res = client.get(f"/roster/{date}")
    assert res.status_code == 404
    assert res.json["message"] == "No roster found for the provided date."

# Test to update a roster entry (status change)
def test_update_roster_status(client):
    date = "2025-05-01"
    room_id = "room001"
    updated_data = {"completed": True}
    
    res = client.put(f"/roster/{date}/{room_id}", json=updated_data)
    assert res.status_code == 200
    assert res.json["data"]["completed"] is True

# Test to delete a roster entry
def test_delete_roster_entry(client):
    date = "2025-05-01"
    room_id = "room001"
    
    res = client.delete(f"/roster/{date}/{room_id}")
    assert res.status_code == 200
    assert res.json["message"] == "Roster entry deleted successfully."
