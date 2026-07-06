from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_event_items(response):
    data = response.json()
    assert "items" in data
    return data["items"]


def create_test_site():
    response = client.post(
        "/sites",
        json={
            "address": f"Event test objektas {uuid4()}",
            "status": "new",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_create_and_list_site_events():
    site = create_test_site()

    create_response = client.post(
        f"/sites/{site['id']}/events",
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

    list_response = client.get(f"/sites/{site['id']}/events")

    assert list_response.status_code == 200

    events = get_event_items(list_response)
    assert len(events) == 1
    assert events[0]["message"] == "Klientas neatsiliepia"


def test_create_site_event_site_not_found():
    response = client.post(
        "/sites/999999999/events",
        json={
            "event_type": "note",
            "message": "Nera tokio objekto",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_list_site_events_site_not_found():
    response = client.get("/sites/999999999/events")

    assert response.status_code == 404
    assert response.json()["detail"] == "Site not found"


def test_create_site_event_rejects_invalid_event_type():
    site = create_test_site()

    response = client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "grybas",
            "message": "Blogas event type",
        },
    )

    assert response.status_code == 422


def test_status_change_creates_site_event():
    site = create_test_site()

    update_response = client.patch(
        f"/sites/{site['id']}",
        json={"status": "blocked"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "blocked"

    events_response = client.get(f"/sites/{site['id']}/events")
    assert events_response.status_code == 200

    events = get_event_items(events_response)
    assert len(events) == 1
    assert events[0]["event_type"] == "status_change"
    assert events[0]["message"] == "Status changed from new to blocked"


def test_same_status_does_not_create_status_change_event():
    site = create_test_site()

    update_response = client.patch(
        f"/sites/{site['id']}",
        json={"status": "new"},
    )

    assert update_response.status_code == 200

    events_response = client.get(f"/sites/{site['id']}/events")
    assert events_response.status_code == 200
    assert get_event_items(events_response) == []


def test_create_site_event_rejects_empty_message():
    site = create_test_site()

    response = client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "",
        },
    )

    assert response.status_code == 422


def test_create_site_event_rejects_whitespace_only_message():
    site = create_test_site()

    response = client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "     ",
        },
    )

    assert response.status_code == 422


def test_create_site_event_strips_message():
    site = create_test_site()

    response = client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "   Signal level checked   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signal level checked"


def test_list_site_events_returns_pagination_metadata():
    site = create_test_site()

    for index in range(2):
        client.post(
            f"/sites/{site['id']}/events",
            json={
                "event_type": "note",
                "message": f"Pagination event {index}",
            },
        )

    response = client.get(f"/sites/{site['id']}/events?limit=1&offset=0")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) == 1


def test_list_site_events_rejects_invalid_limit():
    site = create_test_site()

    response = client.get(f"/sites/{site['id']}/events?limit=0")

    assert response.status_code == 422


def test_list_site_events_rejects_negative_offset():
    site = create_test_site()

    response = client.get(f"/sites/{site['id']}/events?offset=-1")

    assert response.status_code == 422


def test_list_site_events_filters_by_event_type():
    site = create_test_site()

    client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "Regular note",
        },
    )

    client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "issue",
            "message": "Something is wrong",
        },
    )

    response = client.get(f"/sites/{site['id']}/events?event_type=issue")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["event_type"] == "issue"
    assert data["items"][0]["message"] == "Something is wrong"


def test_list_site_events_rejects_invalid_event_type_filter():
    site = create_test_site()

    response = client.get(f"/sites/{site['id']}/events?event_type=bad_type")

    assert response.status_code == 422


def test_list_site_events_sorts_descending():
    site = create_test_site()

    client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "First event",
        },
    )

    client.post(
        f"/sites/{site['id']}/events",
        json={
            "event_type": "note",
            "message": "Second event",
        },
    )

    response = client.get(f"/sites/{site['id']}/events?sort_order=desc")

    assert response.status_code == 200

    events = response.json()["items"]
    assert events[0]["message"] == "Second event"
    assert events[1]["message"] == "First event"


def test_list_site_events_rejects_invalid_sort_order():
    site = create_test_site()

    response = client.get(f"/sites/{site['id']}/events?sort_order=sideways")

    assert response.status_code == 422
