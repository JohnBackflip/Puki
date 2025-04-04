import pytest
from customer import app, db, Guest
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

def test_create_guest(client):
    test_guest = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'address': '123 Main St'
    }
    
    response = client.post('/guests', json=test_guest)
    assert response.status_code == 201
    data = response.json
    assert data['name'] == test_guest['name']
    assert data['email'] == test_guest['email']

def test_get_guest(client):
    # First create a guest
    test_guest = {
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'phone': '+0987654321',
        'address': '456 Oak St'
    }
    create_response = client.post('/guests', json=test_guest)
    guest_id = create_response.json['guest_id']
    
    # Then retrieve it
    response = client.get(f'/guests/{guest_id}')
    assert response.status_code == 200
    data = response.json
    assert data['name'] == test_guest['name']
    assert data['email'] == test_guest['email']

def test_update_guest(client):
    # First create a guest
    test_guest = {
        'name': 'Original Name',
        'email': 'original@example.com',
        'phone': '+1111111111',
        'address': 'Original Address'
    }
    create_response = client.post('/guests', json=test_guest)
    guest_id = create_response.json['guest_id']
    
    # Then update it
    update_data = {
        'name': 'Updated Name',
        'email': 'updated@example.com'
    }
    response = client.put(f'/guests/{guest_id}', json=update_data)
    assert response.status_code == 200
    data = response.json
    assert data['name'] == update_data['name']
    assert data['email'] == update_data['email'] 