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

    list_response = client.get("/sites", headers=auth_headers)

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

    get_response = client.get(f"/sites/{created['id']}", headers=auth_headers)
    assert get_response.status_code == 200

    site = get_response.json()
    assert site["id"] == created["id"]
    assert site["address"] == payload["address"]
    assert site["status"] == "in_progress"


def test_get_site_not_found(auth_headers):
    response = client.get("/sites/999999999", headers=auth_headers)

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

    get_response = client.get(f"/sites/{created['id']}", headers=auth_headers)
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

    response = client.get("/sites?status=blocked", headers=auth_headers)

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1
    assert sites[0]["status"] == "blocked"
    assert "Blocked objektas" in sites[0]["address"]


def test_list_sites_rejects_invalid_status_filter(auth_headers):
    response = client.get("/sites?status=grybas", headers=auth_headers)

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

    response = client.get("/sites/stats", headers=auth_headers)

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

    response = client.get("/sites?search=Vilnius", headers=auth_headers)

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

    response = client.get("/sites?search=Fiber", headers=auth_headers)

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

    response = client.get("/sites?limit=1&offset=1", headers=auth_headers)

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1


def test_list_sites_rejects_limit_below_minimum(auth_headers):
    response = client.get("/sites?limit=0", headers=auth_headers)

    assert response.status_code == 422


def test_list_sites_rejects_limit_above_maximum(auth_headers):
    response = client.get("/sites?limit=101", headers=auth_headers)

    assert response.status_code == 422


def test_list_sites_rejects_negative_offset(auth_headers):
    response = client.get("/sites?offset=-1", headers=auth_headers)

    assert response.status_code == 422


def test_list_sites_rejects_empty_search(auth_headers):
    response = client.get("/sites?search=", headers=auth_headers)

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

    response = client.get("/sites?limit=1&offset=0", headers=auth_headers)

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

    response = client.get("/sites?sort_by=address&sort_order=asc", headers=auth_headers)

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

    response = client.get("/sites?sort_by=address&sort_order=desc", headers=auth_headers)

    assert response.status_code == 200

    sites = get_site_items(response)
    assert sites[0]["address"].startswith("ZZZ")


def test_list_sites_rejects_invalid_sort_by(auth_headers):
    response = client.get("/sites?sort_by=invalid", headers=auth_headers)

    assert response.status_code == 422


def test_list_sites_rejects_invalid_sort_order(auth_headers):
    response = client.get("/sites?sort_order=sideways", headers=auth_headers)

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


def test_create_site_assigns_current_user():
    email = f"site-owner-{uuid4()}@example.com"
    password = "strong-password-123"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 200

    user_id = register_response.json()["id"]

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/sites",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "address": f"Owner test objektas {uuid4()}",
            "status": "new",
        },
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == user_id


def test_list_sites_returns_only_current_user_sites(auth_headers_for_email):
    user_a_headers = auth_headers_for_email(f"user-a-{uuid4()}@example.com")
    user_b_headers = auth_headers_for_email(f"user-b-{uuid4()}@example.com")

    user_a_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"User A objektas {uuid4()}",
            "status": "new",
        },
    )
    assert user_a_response.status_code == 200

    user_b_response = client.post(
        "/sites",
        headers=user_b_headers,
        json={
            "address": f"User B objektas {uuid4()}",
            "status": "new",
        },
    )
    assert user_b_response.status_code == 200

    user_a_list_response = client.get("/sites", headers=user_a_headers)
    assert user_a_list_response.status_code == 200

    items = user_a_list_response.json()["items"]
    addresses = [item["address"] for item in items]

    assert user_a_response.json()["address"] in addresses
    assert user_b_response.json()["address"] not in addresses


def test_get_site_hides_other_users_site(auth_headers_for_email):
    user_a_headers = auth_headers_for_email(f"owner-a-{uuid4()}@example.com")
    user_b_headers = auth_headers_for_email(f"owner-b-{uuid4()}@example.com")

    create_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Private objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    site_id = create_response.json()["id"]

    response = client.get(f"/sites/{site_id}", headers=user_b_headers)

    assert response.status_code == 404


def test_sites_stats_counts_only_current_user_sites(auth_headers_for_email):
    user_a_headers = auth_headers_for_email(f"stats-owner-a-{uuid4()}@example.com")
    user_b_headers = auth_headers_for_email(f"stats-owner-b-{uuid4()}@example.com")

    response_a = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Stats user A {uuid4()}",
            "status": "blocked",
        },
    )
    assert response_a.status_code == 200

    response_b = client.post(
        "/sites",
        headers=user_b_headers,
        json={
            "address": f"Stats user B {uuid4()}",
            "status": "done",
        },
    )
    assert response_b.status_code == 200

    stats_response = client.get("/sites/stats", headers=user_a_headers)

    assert stats_response.status_code == 200
    data = stats_response.json()

    assert data["total"] == 1
    assert data["blocked"] == 1
    assert data["done"] == 0


def test_update_site_hides_other_users_site(auth_headers_for_email):
    user_a_headers = auth_headers_for_email(f"patch-owner-a-{uuid4()}@example.com")
    user_b_headers = auth_headers_for_email(f"patch-owner-b-{uuid4()}@example.com")

    create_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Private patch objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    site_id = create_response.json()["id"]

    response = client.patch(
        f"/sites/{site_id}",
        headers=user_b_headers,
        json={
            "status": "done",
        },
    )

    assert response.status_code == 404


def test_delete_site_hides_other_users_site(auth_headers_for_email):
    user_a_headers = auth_headers_for_email(f"delete-owner-a-{uuid4()}@example.com")
    user_b_headers = auth_headers_for_email(f"delete-owner-b-{uuid4()}@example.com")

    create_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Private delete objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    site_id = create_response.json()["id"]

    response = client.delete(f"/sites/{site_id}", headers=user_b_headers)

    assert response.status_code == 404


def test_create_site_defaults_priority_to_medium(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Default priority objektas {uuid4()}",
            "status": "new",
        },
    )

    assert response.status_code == 200

    site = response.json()
    assert site["priority"] == "medium"


def test_create_site_accepts_high_priority(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"High priority objektas {uuid4()}",
            "status": "new",
            "priority": "high",
        },
    )

    assert response.status_code == 200

    site = response.json()
    assert site["priority"] == "high"


def test_update_site_priority(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Priority update objektas {uuid4()}",
            "status": "new",
            "priority": "medium",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    update_response = client.patch(
        f"/sites/{created['id']}",
        headers=auth_headers,
        json={"priority": "low"},
    )

    assert update_response.status_code == 200

    updated = update_response.json()
    assert updated["id"] == created["id"]
    assert updated["priority"] == "low"


def test_list_sites_filters_by_priority(auth_headers):
    high_address = f"High priority filter {uuid4()}"
    low_address = f"Low priority filter {uuid4()}"

    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": high_address,
            "status": "new",
            "priority": "high",
        },
    )

    client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": low_address,
            "status": "new",
            "priority": "low",
        },
    )

    response = client.get("/sites?priority=high", headers=auth_headers)

    assert response.status_code == 200

    sites = get_site_items(response)
    assert len(sites) == 1
    assert sites[0]["priority"] == "high"
    assert sites[0]["address"] == high_address


def test_create_site_rejects_invalid_priority(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Invalid priority objektas {uuid4()}",
            "status": "new",
            "priority": "grybas",
        },
    )

    assert response.status_code == 422


def test_create_site_with_planned_date(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Planned date objektas {uuid4()}",
            "status": "new",
            "priority": "medium",
            "planned_date": "2026-07-15",
        },
    )

    assert response.status_code == 200

    site = response.json()
    assert site["planned_date"] == "2026-07-15"


def test_update_site_planned_date(auth_headers):
    create_response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Update planned date objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    created = create_response.json()

    update_response = client.patch(
        f"/sites/{created['id']}",
        headers=auth_headers,
        json={"planned_date": "2026-08-01"},
    )

    assert update_response.status_code == 200

    updated = update_response.json()
    assert updated["planned_date"] == "2026-08-01"


def test_create_site_rejects_invalid_planned_date(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Invalid planned date objektas {uuid4()}",
            "status": "new",
            "planned_date": "not-a-date",
        },
    )

    assert response.status_code == 422
