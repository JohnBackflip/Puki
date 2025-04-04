import pytest
from room import app, db, Room
from datetime import datetime

@pytest.fixture
def client(app, db):
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_create_room(client):
    test_room = {
        'room_id': '101',
        'room_type': 'Single',
        'price': 100.00,
        'status': 'AVAILABLE'
    }
    
    response = client.post('/rooms', json=test_room)
    assert response.status_code == 201
    data = response.json
    assert data['room_id'] == test_room['room_id']
    assert data['status'] == test_room['status']

def test_get_room(client):
    # First create a room
    test_room = {
        'room_id': '102',
        'room_type': 'Double',
        'price': 150.00,
        'status': 'AVAILABLE'
    }
    create_response = client.post('/rooms', json=test_room)
    room_id = create_response.json['room_id']
    
    # Then retrieve it
    response = client.get(f'/rooms/{room_id}')
    assert response.status_code == 200
    data = response.json
    assert data['room_id'] == test_room['room_id']
    assert data['room_type'] == test_room['room_type']

def test_update_room_status(client):
    # First create a room
    test_room = {
        'room_id': '103',
        'room_type': 'Suite',
        'price': 200.00,
        'status': 'AVAILABLE'
    }
    create_response = client.post('/rooms', json=test_room)
    room_id = create_response.json['room_id']
    
    # Then update its status
    update_data = {
        'status': 'OCCUPIED'
    }
    response = client.put(f'/rooms/{room_id}/status', json=update_data)
    assert response.status_code == 200
    data = response.json
    assert data['status'] == update_data['status'] 