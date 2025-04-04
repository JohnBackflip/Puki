import pytest
from unittest.mock import patch, MagicMock
from notification import app

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

@patch('notification_service.MessagingClient')
def test_send_sms(mock_messaging_client, client):
    # Mock the messaging client
    mock_client = MagicMock()
    mock_messaging_client.return_value = mock_client
    mock_client.message.return_value = {'status': {'code': 0}}
    
    test_data = {
        'phone_number': '+1234567890',
        'message': 'Test message'
    }
    
    response = client.post('/notifications/sms', json=test_data)
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    
    # Verify the mock was called correctly
    mock_client.message.assert_called_once()

def test_send_notification(client):
    test_data = {
        'recipient': 'test@example.com',
        'subject': 'Test Subject',
        'message': 'Test message'
    }
    
    response = client.post('/notifications/email', json=test_data)
    assert response.status_code == 200
    assert response.json['status'] == 'success' 