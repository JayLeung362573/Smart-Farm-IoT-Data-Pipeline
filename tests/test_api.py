from fastapi.testclient import TestClient
from src.api import app


client = TestClient(app)


def test_health_check_returns_online_status():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "Smart Farm API is responding"
    }