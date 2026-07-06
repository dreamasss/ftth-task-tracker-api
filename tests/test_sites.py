from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_site_items(response):
    data = response.json()
    assert "items" in data
    return data["items"]


def test_create_and_list_sites(auth_headers):
    address = f"Rokiskis, Testo g. {uuid4()}"

    payload = {
        "address": address,
        "customer_name": "Test klientas",
        "status": "new",
        "comment": "Testinis objektas",
    }

    create_response = client.post("/sites", json=payload, headers=auth_headers)

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


def test_get_site_by_id(auth_headers):
    payload = {
        "address": f"Panevezys, Objekto g. {uuid4()}",
        "customer_name": "Vienas klientas",
        "status": "in_progress",
        "comment": "Objekto perziura",
    }

    create_response = client.post("/sites", json=payload, headers=auth_headers)
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


def test_update_site(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
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
        headers=auth_headers,
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


def test_update_site_not_found(auth_headers):
    response = client.patch(
        "/sites/999999999",
        headers=auth_headers,
        json={"status": "done"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_delete_site(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Kaunas, Trinimo g. {uuid4()}",
            "customer_name": "Trinamas klientas",
            "status": "new",
            "comment": "Bus istrintas",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    delete_response = client.delete(f"/sites/{created['id']}", headers=auth_headers)

    assert delete_response.status_code == 200
    assert delete_response.json() == {"deleted": True, "id": created["id"]}

    get_response = client.get(f"/sites/{created['id']}")
    assert get_response.status_code == 404


def test_delete_site_not_found(auth_headers):
    response = client.delete("/sites/999999999", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_create_site_rejects_invalid_status(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Blogas statusas {uuid4()}",
            "status": "grybas",
        },
    )

    assert response.status_code == 422


def test_update_site_rejects_invalid_status(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Validus objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    update_response = client.patch(
        f"/sites/{created['id']}",
        headers=auth_headers,
        json={"status": "grybas"},
    )

    assert update_response.status_code == 422


def test_list_sites_filters_by_status(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Blocked objektas {uuid4()}",
            "status": "blocked",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Done objektas {uuid4()}",
            "status": "done",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
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


def test_get_sites_stats(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Blocked stats {uuid4()}",
            "status": "blocked",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Done stats {uuid4()}",
            "status": "done",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
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


def test_list_sites_searches_by_address(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Vilnius Paieskos g. {uuid4()}",
            "customer_name": "Klientas A",
            "status": "new",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
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


def test_list_sites_searches_by_customer_name(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Adresas {uuid4()}",
            "customer_name": "Jonas Fiber",
            "status": "new",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
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


def test_list_sites_uses_limit_and_offset(auth_headers):
    for index in range(3):
        client.post(
            "/sites",
            headers=auth_headers,
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


def test_list_sites_returns_pagination_metadata(auth_headers):
    for index in range(2):
        client.post(
            "/sites",
            headers=auth_headers,
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


def test_list_sites_sorts_by_address_ascending(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"ZZZ sort objektas {uuid4()}",
            "status": "new",
        },
    )
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"AAA sort objektas {uuid4()}",
            "status": "new",
        },
    )

    response = client.get("/sites?sort_by=address&sort_order=asc")

    assert response.status_code == 200

    sites = get_site_items(response)
    assert sites[0]["address"].startswith("AAA")


def test_list_sites_sorts_by_address_descending(auth_headers):
    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"AAA sort objektas {uuid4()}",
            "status": "new",
        },
    )
    client.post(
        "/sites",
        headers=auth_headers,
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


def test_update_site_changes_updated_at(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
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
        headers=auth_headers,
        json={
            "comment": "Updated comment",
        },
    )

    assert update_response.status_code == 200

    updated_site = update_response.json()
    assert updated_site["updated_at"] >= old_updated_at
    assert updated_site["comment"] == "Updated comment"


def test_update_site_rejects_empty_body(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Empty update objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={},
    )

    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "No fields to update"


def test_update_site_can_clear_nullable_fields(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Nullable objektas {uuid4()}",
            "customer_name": "Laikinas klientas",
            "status": "new",
            "comment": "Laikinas komentaras",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={
            "customer_name": None,
            "comment": None,
        },
    )

    assert update_response.status_code == 200

    updated_site = update_response.json()
    assert updated_site["customer_name"] is None
    assert updated_site["comment"] is None


def test_update_site_rejects_null_address(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Null address objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={
            "address": None,
        },
    )

    assert update_response.status_code == 422


def test_update_site_rejects_null_status(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Null status objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={
            "status": None,
        },
    )

    assert update_response.status_code == 422


def test_create_site_rejects_empty_address(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": "",
            "status": "new",
        },
    )

    assert response.status_code == 422


def test_create_site_rejects_empty_customer_name(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Validus adresas {uuid4()}",
            "customer_name": "",
            "status": "new",
        },
    )

    assert response.status_code == 422


def test_update_site_rejects_empty_comment(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Empty comment objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={
            "comment": "",
        },
    )

    assert update_response.status_code == 422


def test_create_site_rejects_whitespace_only_address(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": "     ",
            "status": "new",
        },
    )

    assert response.status_code == 422


def test_create_site_strips_text_fields(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": "   Strip test address   ",
            "customer_name": "   Strip klientas   ",
            "status": "new",
            "comment": "   Strip komentaras   ",
        },
    )

    assert response.status_code == 200

    site = response.json()
    assert site["address"] == "Strip test address"
    assert site["customer_name"] == "Strip klientas"
    assert site["comment"] == "Strip komentaras"


def test_update_site_strips_text_fields(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Strip update objektas {uuid4()}",
            "status": "new",
        },
    )

    assert create_response.status_code == 200

    site = create_response.json()

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={
            "comment": "   Naujas komentaras   ",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["comment"] == "Naujas komentaras"


def test_create_site_requires_authentication(auth_headers):
    response = client.post(
        "/sites",
        json={
            "address": f"Unauthorized create {uuid4()}",
            "status": "new",
        },
    )

    assert response.status_code == 401
