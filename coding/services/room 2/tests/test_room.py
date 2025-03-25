import sys
import os
from pathlib import Path

# Set testing environment variable
os.environ["TESTING"] = "true"

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import date, timedelta
from room.main import app
from room.models import RoomType, RoomStatus

client = TestClient(app)

def test_create_room(auth_header, room_test_data, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            room_data = room_test_data["rooms"][0]  # Use first room from test data
            response = client.post(
                "/rooms/",
                headers=auth_header,
                json={
                    "room_number": room_data["room_number"],
                    "room_type": room_data["room_type"],
                    "price_per_night": room_data["price_per_night"],
                    "floor": room_data["floor"]
                }
            )
            
            print("Response body:", response.json())
            assert response.status_code == 200
            data = response.json()
            assert data["room_number"] == room_data["room_number"]
            assert data["room_type"] == room_data["room_type"]
            assert float(data["price_per_night"]) == float(room_data["price_per_night"])
            assert data["floor"] == room_data["floor"]

def test_list_rooms(auth_header, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            response = client.get(
                "/rooms/",
                headers=auth_header,
                params={"skip": 0, "limit": 100}
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

def test_get_room(auth_header, room_test_data, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            # First create a room
            room_data = room_test_data["rooms"][1]  # Use second room from test data
            create_response = client.post(
                "/rooms/",
                headers=auth_header,
                json={
                    "room_number": room_data["room_number"],
                    "room_type": room_data["room_type"],
                    "price_per_night": room_data["price_per_night"],
                    "floor": room_data["floor"]
                }
            )
            assert create_response.status_code == 200
            room_id = create_response.json()["id"]
            
            # Then get the room
            response = client.get(f"/rooms/{room_id}", headers=auth_header)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == room_id

def test_update_room_status(auth_header, room_test_data, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            # First create a room
            room_data = room_test_data["rooms"][2]  # Use third room from test data
            create_response = client.post(
                "/rooms/",
                headers=auth_header,
                json={
                    "room_number": room_data["room_number"],
                    "room_type": room_data["room_type"],
                    "price_per_night": room_data["price_per_night"],
                    "floor": room_data["floor"]
                }
            )
            assert create_response.status_code == 200
            room_id = create_response.json()["id"]
            
            # Then update its status
            response = client.patch(
                f"/rooms/{room_id}/status",
                headers=auth_header,
                json={"status": "occupied"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "occupied"

def test_check_room_availability(auth_header, room_test_data, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            # First create a room
            room_data = room_test_data["rooms"][3]  # Use fourth room from test data
            create_response = client.post(
                "/rooms/",
                headers=auth_header,
                json={
                    "room_number": room_data["room_number"],
                    "room_type": room_data["room_type"],
                    "price_per_night": room_data["price_per_night"],
                    "floor": room_data["floor"]
                }
            )
            assert create_response.status_code == 200
            room_id = create_response.json()["id"]
            
            # Check availability
            check_in = date.today() + timedelta(days=1)
            check_out = date.today() + timedelta(days=3)
            response = client.get(
                f"/rooms/{room_id}/availability",
                headers=auth_header,
                params={
                    "start_date": check_in.isoformat(),
                    "end_date": check_out.isoformat()
                }
            )
            assert response.status_code == 200
            assert isinstance(response.json(), bool)

def test_get_room_availability_by_type(auth_header, room_availability_test_data, mock_auth, mock_cursor):
    with patch("services.room.middleware.auth.require_auth_security", return_value=mock_auth):
        with patch("services.room.database.get_db", return_value=mock_cursor):
            # Add test data to mock cursor
            availability = room_availability_test_data["room_availability"][0]
            test_date = date.fromisoformat(availability["date"])
            mock_cursor.availability = [{
                "date": test_date,
                "room_type": availability["room_type"],
                "available_count": availability["available_count"],
                "base_price": availability["base_price"]
            }]
            
            # Check availability for room type
            response = client.get(
                "/rooms/availability",
                headers=auth_header,
                params={
                    "start_date": test_date.strftime("%Y-%m-%d"),
                    "end_date": test_date.strftime("%Y-%m-%d"),
                    "room_type": availability["room_type"]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data) > 0
            assert data[0]["room_type"] == availability["room_type"]
            assert data[0]["available_count"] == availability["available_count"]
            assert data[0]["base_price"] == availability["base_price"] 