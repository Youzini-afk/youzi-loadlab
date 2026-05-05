from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_health_returns_app_status() -> None:
    client = TestClient(create_app())
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "YouziLoadLab"
    assert body["environment"] in {"development", "test"}
    assert "timestamp" in body
