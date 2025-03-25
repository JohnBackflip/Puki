import pytest
from datetime import datetime, timedelta
from housekeeping.models import CleaningStatus

def test_cleaning_task_creation(test_client):
    """Test creating a cleaning task"""
    # Create a cleaning task
    task_response = test_client.post(
        "/tasks/",
        json={
            "room_id": 101,
            "scheduled_at": datetime.now().isoformat(),
            "notes": "Test cleaning task"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert task_response.status_code == 200
    task_data = task_response.json()
    assert task_data["room_id"] == 101
    assert task_data["status"] == "pending"

def test_cleaning_task_status_updates(test_client):
    """Test the cleaning task status update workflow"""
    # Create a cleaning task
    task_response = test_client.post(
        "/tasks/",
        json={
            "room_id": 102,
            "scheduled_at": datetime.now().isoformat(),
            "notes": "Test cleaning task"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert task_response.status_code == 200
    task_data = task_response.json()
    task_id = task_data["id"]

    # Update task status to IN_PROGRESS
    update_response = test_client.put(
        f"/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "IN_PROGRESS"

    # Update task status to COMPLETED
    update_response = test_client.put(
        f"/tasks/{task_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "COMPLETED"

def test_automatic_cleaning_task_creation(test_client):
    """Test that a cleaning task is automatically created when a room is checked out"""
    # First, create a booking and check it out
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    checkout = (datetime.now() + timedelta(days=4)).isoformat()

    # Create a booking
    booking_response = test_client.post(
        "/tasks/",
        json={
            "room_id": 101,
            "scheduled_at": checkout,
            "notes": "Checkout cleaning"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert booking_response.status_code == 200
    booking_data = booking_response.json()
    assert booking_data["room_id"] == 101
    assert booking_data["status"] == "pending"

def test_cleaning_task_status_updates(test_client):
    """Test the cleaning task status update workflow"""
    # Create a cleaning task
    task_response = test_client.post(
        "/tasks/",
        json={
            "room_id": 102,
            "scheduled_at": datetime.now().isoformat(),
            "notes": "Test cleaning task"
        },
        headers={"Authorization": "Bearer test_token"}
    )
    assert task_response.status_code == 200
    task_data = task_response.json()
    task_id = task_data["id"]

    # Update task status to IN_PROGRESS
    update_response = test_client.put(
        f"/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "IN_PROGRESS"

    # Update task status to COMPLETED
    update_response = test_client.put(
        f"/tasks/{task_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": "Bearer test_token"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "COMPLETED"
    
    # Verify room status is updated to available
    room_response = test_client.get(f"/rooms/102")
    assert room_response.status_code == 200
    assert room_response.json()["status"] == "available" 