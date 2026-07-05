from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_and_list_sites():
    address = f"Rokiskis, Testo g. {uuid4()}"

    payload = {
        "address": address,
        "customer_name": "Test klientas",
        "status": "new",
        "comment": "Testinis objektas",
    }

    create_response = client.post("/sites", json=payload)

    assert create_response.status_code == 200

    created = create_response.json()
    assert created["address"] == address
    assert created["customer_name"] == "Test klientas"
    assert created["status"] == "new"
    assert created["comment"] == "Testinis objektas"
    assert "id" in created
    assert "created_at" in created

    list_response = client.get("/sites")

    assert list_response.status_code == 200

    sites = list_response.json()
    assert any(site["address"] == address for site in sites)


def test_get_site_by_id():
    payload = {
        "address": f"Panevezys, Objekto g. {uuid4()}",
        "customer_name": "Vienas klientas",
        "status": "in_progress",
        "comment": "Objekto perziura",
    }

    create_response = client.post("/sites", json=payload)
    assert create_response.status_code == 200

    created = create_response.json()

    get_response = client.get(f"/sites/{created['id']}")
    assert get_response.status_code == 200

    site = get_response.json()
    assert site["id"] == created["id"]
    assert site["address"] == payload["address"]
    assert site["status"] == "in_progress"


def test_get_site_not_found():
    response = client.get("/sites/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"
