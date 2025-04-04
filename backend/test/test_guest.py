import pytest
from app import app, db, Guest

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_create_guest(client):
    response = client.post("/guests", json={
        "name": "Alice",
        "email": "alice@example.com",
        "contact": "12345678"
    })
    assert response.status_code == 201
    assert response.json["data"]["name"] == "Alice"

def test_get_all_guests(client):
    client.post("/guests", json={
        "name": "Bob",
        "email": "bob@example.com",
        "contact": "98765432"
    })
    response = client.get("/guests")
    assert response.status_code == 200
    assert len(response.json["data"]["guests"]) > 0

def test_update_guest(client):
    post = client.post("/guests", json={
        "name": "Charlie",
        "email": "charlie@example.com",
        "contact": "99999999"
    })
    guest_id = post.json["data"]["guest_id"]
    response = client.patch(f"/guests/{guest_id}", json={"name": "Chuck"})
    assert response.status_code == 200
    assert response.json["data"]["name"] == "Chuck"

def test_delete_guest(client):
    post = client.post("/guests", json={
        "name": "Daisy",
        "email": "daisy@example.com",
        "contact": "11111111"
    })
    guest_id = post.json["data"]["guest_id"]
    response = client.delete(f"/guests/{guest_id}")
    assert response.status_code == 200
