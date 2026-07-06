from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_event_items(response):
    data = response.json()
    assert "items" in data
    return data["items"]


def create_test_site(auth_headers):
    response = client.post(
        "/sites",
        headers=auth_headers,
        json={
            "address": f"Event test objektas {uuid4()}",
            "status": "new",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_list_site_events(auth_headers):
    site = create_test_site(auth_headers)

    create_response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "issue",
            "message": "Klientas neatsiliepia",
        },
    )

    assert create_response.status_code == 200

    event = create_response.json()
    assert event["site_id"] == site["id"]
    assert event["event_type"] == "issue"
    assert event["message"] == "Klientas neatsiliepia"

    list_response = client.get(f"/sites/{site['id']}/events", headers=auth_headers)

    assert list_response.status_code == 200

    events = get_event_items(list_response)
    assert len(events) == 1
    assert events[0]["message"] == "Klientas neatsiliepia"


def test_create_site_event_site_not_found(auth_headers):
    response = client.post(
        "/sites/999999999/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "Nera tokio objekto",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_list_site_events_site_not_found(auth_headers):
    response = client.get("/sites/999999999/events", headers=auth_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_create_site_event_rejects_invalid_event_type(auth_headers):
    site = create_test_site(auth_headers)

    response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "grybas",
            "message": "Blogas event type",
        },
    )

    assert response.status_code == 422


def test_status_change_creates_site_event(auth_headers):
    site = create_test_site(auth_headers)

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={"status": "blocked"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "blocked"

    events_response = client.get(f"/sites/{site['id']}/events", headers=auth_headers)
    assert events_response.status_code == 200

    events = get_event_items(events_response)
    assert len(events) == 1
    assert events[0]["event_type"] == "status_change"
    assert events[0]["message"] == "Status changed from new to blocked"


def test_same_status_does_not_create_status_change_event(auth_headers):
    site = create_test_site(auth_headers)

    update_response = client.patch(
        f"/sites/{site['id']}",
        headers=auth_headers,
        json={"status": "new"},
    )

    assert update_response.status_code == 200

    events_response = client.get(f"/sites/{site['id']}/events", headers=auth_headers)
    assert events_response.status_code == 200
    assert get_event_items(events_response) == []


def test_create_site_event_rejects_empty_message(auth_headers):
    site = create_test_site(auth_headers)

    response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_create_site_event_rejects_whitespace_only_message(auth_headers):
    site = create_test_site(auth_headers)

    response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "     ",
        },
    )

    assert response.status_code == 422


def test_create_site_event_strips_message(auth_headers):
    site = create_test_site(auth_headers)

    response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "   Signal level checked   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signal level checked"


def test_list_site_events_returns_pagination_metadata(auth_headers):
    site = create_test_site(auth_headers)

    for index in range(2):
        client.post(
            f"/sites/{site['id']}/events",
            headers=auth_headers,
            json={
                "event_type": "note",
                "message": f"Pagination event {index}",
            },
        )

    response = client.get(f"/sites/{site['id']}/events?limit=1&offset=0", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1


def test_list_site_events_rejects_invalid_limit(auth_headers):
    site = create_test_site(auth_headers)

    response = client.get(f"/sites/{site['id']}/events?limit=0", headers=auth_headers)

    assert response.status_code == 422


def test_list_site_events_rejects_negative_offset(auth_headers):
    site = create_test_site(auth_headers)

    response = client.get(f"/sites/{site['id']}/events?offset=-1", headers=auth_headers)

    assert response.status_code == 422


def test_list_site_events_filters_by_event_type(auth_headers):
    site = create_test_site(auth_headers)

    client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "Regular note",
        },
    )

    client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "issue",
            "message": "Something is wrong",
        },
    )

    response = client.get(f"/sites/{site['id']}/events?event_type=issue", headers=auth_headers)

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["event_type"] == "issue"
    assert data["items"][0]["message"] == "Something is wrong"


def test_list_site_events_rejects_invalid_event_type_filter(auth_headers):
    site = create_test_site(auth_headers)

    response = client.get(f"/sites/{site['id']}/events?event_type=bad_type", headers=auth_headers)

    assert response.status_code == 422


def test_list_site_events_sorts_descending(auth_headers):
    site = create_test_site(auth_headers)

    client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "First event",
        },
    )

    client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "Second event",
        },
    )

    response = client.get(f"/sites/{site['id']}/events?sort_order=desc", headers=auth_headers)

    assert response.status_code == 200

    events = response.json()["items"]
    assert events[0]["message"] == "Second event"
    assert events[1]["message"] == "First event"


def test_list_site_events_rejects_invalid_sort_order(auth_headers):
    site = create_test_site(auth_headers)

    response = client.get(f"/sites/{site['id']}/events?sort_order=sideways", headers=auth_headers)

    assert response.status_code == 422


def test_create_site_event_updates_site_updated_at(auth_headers):
    site = create_test_site(auth_headers)
    old_updated_at = site["updated_at"]

    event_response = client.post(
        f"/sites/{site['id']}/events",
        headers=auth_headers,
        json={
            "event_type": "note",
            "message": "Updated site timestamp through event",
        },
    )

    assert event_response.status_code == 200

    site_response = client.get(f"/sites/{site['id']}", headers=auth_headers)
    assert site_response.status_code == 200

    updated_site = site_response.json()
    assert updated_site["updated_at"] != old_updated_at


def test_create_site_event_requires_authentication(auth_headers):
    site = create_test_site(auth_headers)

    response = client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "Unauthorized event",
        },
    )

    assert response.status_code == 401


def make_site_event_auth_headers(email: str):
    password = "strong-password-123"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_site_events_hides_other_users_site():
    user_a_headers = make_site_event_auth_headers(f"events-owner-a-{uuid4()}@example.com")
    user_b_headers = make_site_event_auth_headers(f"events-owner-b-{uuid4()}@example.com")

    create_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Private events objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    site_id = create_response.json()["id"]

    response = client.get(f"/sites/{site_id}/events", headers=user_b_headers)

    assert response.status_code == 404


def test_create_site_event_hides_other_users_site():
    user_a_headers = make_site_event_auth_headers(f"event-create-owner-a-{uuid4()}@example.com")
    user_b_headers = make_site_event_auth_headers(f"event-create-owner-b-{uuid4()}@example.com")

    create_response = client.post(
        "/sites",
        headers=user_a_headers,
        json={
            "address": f"Private event create objektas {uuid4()}",
            "status": "new",
        },
    )
    assert create_response.status_code == 200

    site_id = create_response.json()["id"]

    response = client.post(
        f"/sites/{site_id}/events",
        headers=user_b_headers,
        json={
            "event_type": "note",
            "message": "Trying to write to another users site",
        },
    )

    assert response.status_code == 404
