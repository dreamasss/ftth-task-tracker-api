from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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

    events = list_response.json()
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

    events = events_response.json()
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
    assert events_response.json() == []
