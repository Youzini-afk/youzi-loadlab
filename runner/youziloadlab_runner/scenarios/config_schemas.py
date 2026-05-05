from typing import Any


FIREWORKS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["setup", "request", "loadProfile", "cleanup"],
    "properties": {
        "setup": {
            "type": "object",
            "properties": {
                "createUsers": {"type": "boolean", "default": True},
                "testUserPrefix": {"type": "string", "default": "stress_test_fw_"},
                "testUserCount": {"type": "integer", "default": 3, "minimum": 1, "maximum": 100},
                "testUserGroup": {"type": "string", "default": "fireworks_stress"},
                "quotaPerUser": {"type": "integer", "default": 500000000, "minimum": 1},
                "discordGateExempt": {"type": "boolean", "default": True},
                "createChannel": {"type": "boolean", "default": True},
                "channelName": {"type": "string", "default": "fireworks_stress_main"},
                "channelType": {"type": "integer", "default": 41},
                "fireworksBaseUrl": {
                    "type": "string",
                    "default": "https://api.fireworks.ai/inference/v1",
                },
            },
        },
        "request": {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "default": "accounts/fireworks/models/llama-v3p1-8b-instruct",
                },
                "prompt": {"type": "string", "default": "Say hello in 50 words or less."},
                "maxTokens": {"type": "integer", "default": 128, "minimum": 1, "maximum": 4096},
                "temperature": {"type": "number", "default": 0.7, "minimum": 0, "maximum": 2},
                "streamRatio": {"type": "number", "default": 0.1, "minimum": 0, "maximum": 1},
                "timeoutSeconds": {"type": "integer", "default": 30, "minimum": 1, "maximum": 300},
            },
        },
        "loadProfile": {"type": "object", "properties": {"phases": {"type": "array"}}},
        "cleanup": {
            "type": "object",
            "properties": {
                "deleteUsers": {"type": "boolean", "default": False},
                "deleteTokens": {"type": "boolean", "default": True},
                "disableCreatedChannel": {"type": "boolean", "default": True},
            },
        },
    },
}

POLLING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["polling", "loadProfile"],
    "properties": {
        "polling": {
            "type": "object",
            "properties": {
                "channelListIntervalSeconds": {"type": "integer", "default": 5, "minimum": 1},
                "tokenListIntervalSeconds": {"type": "integer", "default": 10, "minimum": 1},
                "usageIntervalSeconds": {"type": "integer", "default": 15, "minimum": 1},
                "includeForegroundChat": {"type": "boolean", "default": True},
                "foregroundChatRatio": {"type": "number", "default": 0.3, "minimum": 0, "maximum": 1},
            },
        },
        "loadProfile": {"type": "object", "properties": {"phases": {"type": "array"}}},
    },
}
