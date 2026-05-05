from typing import Any

CORE_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "openai-chat-load",
        "title": "OpenAI-Compatible Chat Load",
        "description": "Generic /v1/chat/completions pressure test for OpenAI-compatible gateways.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["request", "loadProfile"]},
        "enabled": True,
    },
    {
        "id": "nashiyard-fireworks-channel",
        "title": "NashiYard Fireworks Channel Stress",
        "description": "Creates isolated NashiYard test users/tokens/channels and stresses Fireworks routing.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["setup", "request", "loadProfile", "cleanup"]},
        "enabled": True,
    },
    {
        "id": "nashiyard-polling-system",
        "title": "NashiYard Polling System Stress",
        "description": "Stresses polling-style admin/background workflows and their interaction with API traffic.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["polling", "loadProfile"]},
        "enabled": True,
    },
    {
        "id": "smoke-check",
        "title": "Smoke Check",
        "description": "Short preflight run for auth, model availability, token usability, and sanitization checks.",
        "version": "0.1.0",
        "schema_json": {"type": "object", "required": ["targetId"]},
        "enabled": True,
    },
]


def list_core_scenarios() -> list[dict[str, Any]]:
    return CORE_SCENARIOS
