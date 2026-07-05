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


def test_update_site():
    create_response = client.post(
        "/sites",
        json={
            "address": f"Vilnius, Darbo g. {uuid4()}",
            "customer_name": "Pradinis klientas",
            "status": "new",
            "comment": "Dar nepradeta",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    update_response = client.patch(
        f"/sites/{created['id']}",
        json={
            "status": "blocked",
            "comment": "Truksta leidimo",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["address"] == created["address"]
    assert updated["status"] == "blocked"
    assert updated["comment"] == "Truksta leidimo"


def test_update_site_not_found():
    response = client.patch(
        "/sites/999999999",
        json={"status": "done"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_delete_site():
    create_response = client.post(
        "/sites",
        json={
            "address": f"Kaunas, Trinimo g. {uuid4()}",
            "customer_name": "Trinamas klientas",
            "status": "new",
            "comment": "Bus istrintas",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    delete_response = client.delete(f"/sites/{created['id']}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "id": created["id"]}

    get_response = client.get(f"/sites/{created['id']}")
    assert get_response.status_code == 404


def test_delete_site_not_found():
    response = client.delete("/sites/999999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_create_site_rejects_invalid_status():
    response = client.post(
        "/sites",
        json={
            "address": f"Blogas statusas {uuid4()}",
            "status": "grybas",
        },
    )

    assert response.status_code == 422


def test_update_site_rejects_invalid_status():
    create_response = client.post(
        "/sites",
        json={
            "address": f"Validus objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    update_response = client.patch(
        f"/sites/{created['id']}",
        json={"status": "grybas"},
    )

    assert update_response.status_code == 422


def test_list_sites_filters_by_status():
    client.post(
        "/sites",
        json={
            "address": f"Blocked objektas {uuid4()}",
            "status": "blocked",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Done objektas {uuid4()}",
            "status": "done",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Progress objektas {uuid4()}",
            "status": "in_progress",
        },
    )

    response = client.get("/sites?status=blocked")

    assert response.status_code == 200

    sites = response.json()
    assert len(sites) == 1
    assert sites[0]["status"] == "blocked"
    assert "Blocked objektas" in sites[0]["address"]


def test_list_sites_rejects_invalid_status_filter():
    response = client.get("/sites?status=grybas")

    assert response.status_code == 422
