import base64
import hashlib
import hmac
import json
import time
from typing import Any

SESSION_COOKIE_NAME = "youziloadlab_session"
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_session_token(
    *,
    app_secret_key: str,
    subject: str = "admin",
    now: int | None = None,
    max_age_seconds: int = SESSION_MAX_AGE_SECONDS,
) -> str:
    issued_at = int(time.time()) if now is None else now
    payload = {"sub": subject, "iat": issued_at, "exp": issued_at + max_age_seconds}
    encoded_payload = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    return f"{encoded_payload}.{_sign(encoded_payload, app_secret_key)}"


def verify_session_token(
    token: str | None,
    *,
    app_secret_key: str,
    now: int | None = None,
) -> dict[str, Any] | None:
    if not token or "." not in token:
        return None
    encoded_payload, signature = token.rsplit(".", 1)
    expected_signature = _sign(encoded_payload, app_secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        payload = json.loads(_b64decode(encoded_payload))
    except (ValueError, json.JSONDecodeError):
        return None
    current_time = int(time.time()) if now is None else now
    if int(payload.get("exp", 0)) < current_time:
        return None
    return payload if payload.get("sub") == "admin" else None

