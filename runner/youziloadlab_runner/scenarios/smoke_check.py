from typing import TypedDict


class SmokeCheck(TypedDict):
    name: str
    method: str
    path: str


def build_smoke_checks() -> list[SmokeCheck]:
    return [
        {"name": "health", "method": "GET", "path": "/api/health"},
        {"name": "models", "method": "GET", "path": "/v1/models"},
        {"name": "chat", "method": "POST", "path": "/v1/chat/completions"},
        {"name": "invalid_key_sanitization", "method": "POST", "path": "/v1/chat/completions"},
    ]
