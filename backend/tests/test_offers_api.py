from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_offers():
    response = client.get("/api/v1/offers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data

def test_offer_filter_options():
    response = client.get("/api/v1/offers/filters")
    assert response.status_code == 200