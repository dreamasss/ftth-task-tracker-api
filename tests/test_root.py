from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_api_metadata():
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "FTTH Task Tracker API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "ok"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"
