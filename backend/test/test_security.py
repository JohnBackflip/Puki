import pytest
from security import app, db, Keycard
from datetime import datetime, timedelta

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

def test_issue_keycard(client):
    test_keycard = {
        'room_id': '101',
        'guest_id': 1,
        'valid_from': datetime.now().isoformat(),
        'valid_to': (datetime.now() + timedelta(days=3)).isoformat()
    }
    
    response = client.post('/keycards', json=test_keycard)
    assert response.status_code == 201
    data = response.json
    assert data['room_id'] == test_keycard['room_id']
    assert data['guest_id'] == test_keycard['guest_id']
    assert 'pin' in data

def test_get_keycard(client):
    # First create a keycard
    test_keycard = {
        'room_id': '102',
        'guest_id': 2,
        'valid_from': datetime.now().isoformat(),
        'valid_to': (datetime.now() + timedelta(days=3)).isoformat()
    }
    create_response = client.post('/keycards', json=test_keycard)
    keycard_id = create_response.json['keycard_id']
    
    # Then retrieve it
    response = client.get(f'/keycards/{keycard_id}')
    assert response.status_code == 200
    data = response.json
    assert data['room_id'] == test_keycard['room_id']
    assert data['guest_id'] == test_keycard['guest_id']

def test_validate_keycard(client):
    # First create a keycard
    test_keycard = {
        'room_id': '103',
        'guest_id': 3,
        'valid_from': datetime.now().isoformat(),
        'valid_to': (datetime.now() + timedelta(days=3)).isoformat()
    }
    create_response = client.post('/keycards', json=test_keycard)
    keycard_id = create_response.json['keycard_id']
    pin = create_response.json['pin']
    
    # Then validate it
    validate_data = {
        'pin': pin
    }
    response = client.post(f'/keycards/{keycard_id}/validate', json=validate_data)
    assert response.status_code == 200
    assert response.json['valid'] == True 