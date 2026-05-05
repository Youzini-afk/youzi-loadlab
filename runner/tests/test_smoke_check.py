from youziloadlab_runner.scenarios.smoke_check import build_smoke_checks


def test_smoke_checks_cover_health_models_chat_and_sanitization() -> None:
    checks = build_smoke_checks()
    assert [check["name"] for check in checks] == [
        "health",
        "models",
        "chat",
        "invalid_key_sanitization",
    ]
    assert checks[0]["method"] == "GET"
    assert checks[2]["path"] == "/v1/chat/completions"
