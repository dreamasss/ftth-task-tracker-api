from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_site_items(response):
    data = response.json()
    assert "items" in data
    return data["items"]


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

    sites = get_site_items(list_response)
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

    sites = get_site_items(response)
    assert len(sites) == 1
    assert sites[0]["status"] == "blocked"
    assert "Blocked objektas" in sites[0]["address"]


def test_list_sites_rejects_invalid_status_filter():
    response = client.get("/sites?status=grybas")

    assert response.status_code == 422


def test_get_sites_stats():
    client.post(
        "/sites",
        json={
            "address": f"Blocked stats {uuid4()}",
            "status": "blocked",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Done stats {uuid4()}",
            "status": "done",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Done stats 2 {uuid4()}",
            "status": "done",
        },
    )

    response = client.get("/sites/stats")

    assert response.status_code == 200

    stats = response.json()
    assert stats["new"] == 0
    assert stats["in_progress"] == 0
    assert stats["blocked"] == 1
    assert stats["done"] == 2
    assert stats["reported"] == 0


def test_list_sites_searches_by_address():
    client.post(
        "/sites",
        json={
            "address": f"Vilnius Paieskos g. {uuid4()}",
            "customer_name": "Klientas A",
            "status": "new",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Kaunas Kita g. {uuid4()}",
            "customer_name": "Klientas B",
            "status": "new",
        },
    )

    response = client.get("/sites?search=Vilnius")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1
    assert "Vilnius" in sites[0]["address"]


def test_list_sites_searches_by_customer_name():
    client.post(
        "/sites",
        json={
            "address": f"Adresas {uuid4()}",
            "customer_name": "Jonas Fiber",
            "status": "new",
        },
    )

    client.post(
        "/sites",
        json={
            "address": f"Adresas {uuid4()}",
            "customer_name": "Petras Kabelis",
            "status": "new",
        },
    )

    response = client.get("/sites?search=Fiber")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1
    assert sites[0]["customer_name"] == "Jonas Fiber"


def test_list_sites_uses_limit_and_offset():
    for index in range(3):
        client.post(
            "/sites",
            json={
                "address": f"Pagination objektas {index} {uuid4()}",
                "status": "new",
            },
        )

    response = client.get("/sites?limit=1&offset=1")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1


def test_list_sites_rejects_limit_below_minimum():
    response = client.get("/sites?limit=0")

    assert response.status_code == 422


def test_list_sites_rejects_limit_above_maximum():
    response = client.get("/sites?limit=101")

    assert response.status_code == 422


def test_list_sites_rejects_negative_offset():
    response = client.get("/sites?offset=-1")

    assert response.status_code == 422


def test_list_sites_rejects_empty_search():
    response = client.get("/sites?search=")

    assert response.status_code == 422


def test_list_sites_returns_pagination_metadata():
    for index in range(2):
        client.post(
            "/sites",
            json={
                "address": f"Metadata objektas {index} {uuid4()}",
                "status": "new",
            },
        )

    response = client.get("/sites?limit=1&offset=0")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1


def test_list_sites_sorts_by_address_ascending():
    client.post(
        "/sites",
        json={
            "address": f"ZZZ sort objektas {uuid4()}",
            "status": "new",
        },
    )
    client.post(
        "/sites",
        json={
            "address": f"AAA sort objektas {uuid4()}",
            "status": "new",
        },
    )

    response = client.get("/sites?sort_by=address&sort_order=asc")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert sites[0]["address"].startswith("AAA")


def test_list_sites_sorts_by_address_descending():
    client.post(
        "/sites",
        json={
            "address": f"AAA sort objektas {uuid4()}",
            "status": "new",
        },
    )
    client.post(
        "/sites",
        json={
            "address": f"ZZZ sort objektas {uuid4()}",
            "status": "new",
        },
    )

    response = client.get("/sites?sort_by=address&sort_order=desc")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert sites[0]["address"].startswith("ZZZ")


def test_list_sites_rejects_invalid_sort_by():
    response = client.get("/sites?sort_by=invalid")

    assert response.status_code == 422


def test_list_sites_rejects_invalid_sort_order():
    response = client.get("/sites?sort_order=sideways")

    assert response.status_code == 422


def test_update_site_changes_updated_at():
    create_response = client.post(
        "/sites",
        json={
            "address": f"Updated at objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    created_site = create_response.json()
    old_updated_at = created_site["updated_at"]

    update_response = client.patch(
        f"/sites/{created_site['id']}",
        json={
            "comment": "Updated comment",
        },
    )

    assert update_response.status_code == 200

    updated_site = update_response.json()
    assert updated_site["updated_at"] >= old_updated_at
    assert updated_site["comment"] == "Updated comment"
