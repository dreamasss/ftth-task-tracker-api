from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_db():
    response = client.get("/health/db")

    assert response.status_code == 200

    data = response.json()
    assert data["db"] == "ok"
    assert "PostgreSQL" in data["version"]
