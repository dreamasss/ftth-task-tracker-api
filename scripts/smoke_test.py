#!/usr/bin/env python3

import json
import os
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")


def request(method, path, data=None, token=None):
    body = None
    headers = {}

    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token is not None:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as error:
        raw = error.read().decode("utf-8")
        print(f"Request failed: {method} {path} -> {error.code}")
        print(raw)
        sys.exit(1)


def main():
    email = f"smoke-{uuid4()}@example.com"
    password = "strong-password-123"

    status, root = request("GET", "/")
    assert status == 200
    assert root["name"] == "FTTH Task Tracker API"
    assert root["version"] == "1.0.0"
    assert root["status"] == "ok"
    assert root["docs"] == "/docs"
    assert root["health"] == "/health"

    status, health = request("GET", "/health")
    assert status == 200
    assert health["status"] == "ok"

    status, _user = request(
        "POST",
        "/auth/register",
        {"email": email, "password": password},
    )
    assert status == 200

    status, token_response = request(
        "POST",
        "/auth/login",
        {"email": email, "password": password},
    )
    assert status == 200

    token = token_response["access_token"]

    status, site = request(
        "POST",
        "/sites",
        {
            "address": f"Smoke test site {uuid4()}",
            "status": "new",
            "priority": "high",
            "comment": "Created by smoke test",
        },
        token,
    )
    assert status == 200

    site_id = site["id"]
    assert site["priority"] == "high"

    status, priority_sites = request("GET", "/sites?priority=high", token=token)
    assert status == 200
    assert any(item["id"] == site_id for item in priority_sites["items"])

    status, sites = request("GET", "/sites", token=token)
    assert status == 200
    assert sites["total"] >= 1

    status, _event = request(
        "POST",
        f"/sites/{site_id}/events",
        {"event_type": "note", "message": "Smoke test event"},
        token,
    )
    assert status == 200

    status, stats = request("GET", "/sites/stats", token=token)
    assert status == 200
    assert stats["total"] >= 1

    print(f"Smoke test passed for {BASE_URL}")


if __name__ == "__main__":
    main()
