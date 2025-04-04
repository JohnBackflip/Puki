import pytest
from housekeeping import app, invokes

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_housekeeping(client, monkeypatch):
    def mock_invoke_http(url, method='GET', json=None, **kwargs):
        if url == 'http://localhost:4001/roster':
            return {'code': 200, 'message': 'Housekeeper assigned'}
        elif url == 'http://localhost:5006/rooms/room001/update-status':
            return {'code': 200, 'message': 'Room status updated'}
        elif url == 'http://localhost:5002/bookings/active/room001':
            return {'code': 404, 'message': 'Room is vacant'}
        return {'code': 500, 'message': 'Error'}

    monkeypatch.setattr('invokes.invoke_http', mock_invoke_http)

    res = client.post("/housekeeping", json={"room_id": "room001"})
    assert res.status_code == 200
    assert res.json["message"] == "Cleaning started for room room001"
