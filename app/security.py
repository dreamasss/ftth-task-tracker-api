import hashlib
import hmac
import os
from base64 import b64decode, b64encode
from datetime import datetime, timedelta, timezone

import jwt
from jwt import InvalidTokenError

PBKDF2_ITERATIONS = 600_000
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        b64encode(salt).decode("ascii"),
        b64encode(password_hash).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, iterations_text, salt_text, hash_text = stored_hash.split("$", 3)

    if algorithm != "pbkdf2_sha256":
        return False

    iterations = int(iterations_text)
    salt = salt_text.encode("ascii")
    expected_hash = hash_text.encode("ascii")

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        b64decode(salt),
        iterations,
    )

    return hmac.compare_digest(
        b64encode(password_hash).decode("ascii"),
        expected_hash.decode("ascii"),
    )


def create_access_token(user_id: int, expires_in_seconds: int = 3600) -> str:
    secret = os.getenv("SECRET_KEY", "dev-secret-change-me-minimum-32-bytes")
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=expires_in_seconds),
    }

    return jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    secret = os.getenv("SECRET_KEY", "dev-secret-change-me-minimum-32-bytes")

    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        return None
