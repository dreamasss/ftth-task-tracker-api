from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_contains_response_schemas():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schemas = response.json()["components"]["schemas"]

    assert "SiteRead" in schemas
    assert "SiteListResponse" in schemas
    assert "SiteStatsResponse" in schemas
    assert "SiteEventRead" in schemas
    assert "SiteEventListResponse" in schemas
    assert "SiteDeleteResponse" in schemas
