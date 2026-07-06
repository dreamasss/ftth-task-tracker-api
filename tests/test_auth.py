from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import SessionLocal
from app.main import app
from app.models import User
from app.security import verify_password

client = TestClient(app)


def test_register_user():
    email = f"user-{uuid4()}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "strong-password-123",
        },
    )

    assert response.status_code == 200

    user = response.json()
    assert user["email"] == email
    assert user["is_active"] is True
    assert "id" in user
    assert "created_at" in user
    assert "hashed_password" not in user

    with SessionLocal() as db:
        db_user = db.execute(select(User).where(User.email == email)).scalar_one()

        assert db_user.hashed_password != "strong-password-123"
        assert verify_password("strong-password-123", db_user.hashed_password)


def test_register_user_normalizes_email():
    response = client.post(
        "/auth/register",
        json={
            "email": "  TestUser@Example.COM  ",
            "password": "strong-password-123",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "testuser@example.com"


def test_register_user_rejects_duplicate_email():
    email = f"duplicate-{uuid4()}@example.com"

    first_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "strong-password-123",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "another-password-123",
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Email already registered"


def test_register_user_rejects_short_password():
    response = client.post(
        "/auth/register",
        json={
            "email": f"short-password-{uuid4()}@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_register_user_rejects_invalid_email():
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "strong-password-123",
        },
    )

    assert response.status_code == 422
