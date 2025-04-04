import requests

BASE_URL = "http://localhost:8000"

# Test data
new_price = {
    "room_type": "Single",
    "price": 120.50
}

updated_price = {
    "room_type": "Single",
    "price": 145.75
}

def test_create_price():
    res = requests.post(f"{BASE_URL}/prices/", json=new_price)
    print("✅ Create Price:", res.status_code, res.json())

def test_get_all_prices():
    res = requests.get(f"{BASE_URL}/prices/")
    print("📦 All Prices:", res.status_code, res.json())

def test_get_price_by_type():
    res = requests.get(f"{BASE_URL}/prices/Single")
    print("🔎 Get Single Price:", res.status_code, res.json())

def test_update_price():
    res = requests.put(f"{BASE_URL}/prices/Single", json=updated_price)
    print("✏️ Update Price:", res.status_code, res.json())

def test_get_nonexistent_price():
    res = requests.get(f"{BASE_URL}/prices/NonExistent")
    print("❌ Nonexistent Price:", res.status_code, res.text)

def test_adjust_prices_by_season(client):
    # Add a second price
    client.post("/prices/", json={"room_type": "Suite", "price": 200.0})

    res = client.post("/prices/events/festive", json={"season": "Christmas"})
    assert res.status_code == 200
    updates = res.json["updated"]
    for upd in updates:
        if upd["room_type"] == "Deluxe":
            assert upd["new"] == round(150.0 * 1.25, 2)
        if upd["room_type"] == "Suite":
            assert upd["new"] == round(200.0 * 1.25, 2)

if __name__ == "__main__":
    test_create_price()
    test_get_all_prices()
    test_get_price_by_type()
    test_update_price()
    test_get_nonexistent_price()
