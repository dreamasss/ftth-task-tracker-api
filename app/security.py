import hashlib
import hmac
import os
from base64 import b64encode

PBKDF2_ITERATIONS = 600_000


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
        __import__("base64").b64decode(salt),
        iterations,
    )

    return hmac.compare_digest(
        b64encode(password_hash).decode("ascii"),
        expected_hash.decode("ascii"),
    )


def create_access_token(user_id: int) -> str:
    import json
    import time

    secret = os.getenv("SECRET_KEY", "dev-secret-change-me")
    payload = {
        "sub": str(user_id),
        "iat": int(time.time()),
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    payload_b64 = b64encode(payload_json.encode("utf-8")).decode("ascii")

    signature = hmac.new(
        secret.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload_b64}.{signature}"
