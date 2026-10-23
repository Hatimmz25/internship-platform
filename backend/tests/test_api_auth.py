from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration_and_login():
    # Register test user
    reg_payload = {
        "email": "testsubscriber@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code in (200, 201, 400)  # 400 if user already exists

    # Login test user
    login_payload = {
        "username": "testsubscriber@example.com",
        "password": "Password123!"
    }
    response = client.post("/api/v1/auth/login", data=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"