from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_scenarios_include_v1_core_suites() -> None:
    client = TestClient(create_app())
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert "openai-chat-load" in ids
    assert "nashiyard-fireworks-channel" in ids
    assert "nashiyard-polling-system" in ids
    assert "smoke-check" in ids
