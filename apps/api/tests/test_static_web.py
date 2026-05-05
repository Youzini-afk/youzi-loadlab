from pathlib import Path

from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_static_web_root_spa_fallback_and_api_routes_remain_available(tmp_path: Path) -> None:
    index_html = "<!doctype html><html><body><div id=\"root\">YouziLoadLab</div></body></html>"
    (tmp_path / "index.html").write_text(index_html, encoding="utf-8")

    client = TestClient(create_app(static_dir=tmp_path))

    root_response = client.get("/")
    assert root_response.status_code == 200
    assert "text/html" in root_response.headers["content-type"]
    assert "YouziLoadLab" in root_response.text

    spa_response = client.get("/runs/example-run")
    assert spa_response.status_code == 200
    assert "text/html" in spa_response.headers["content-type"]
    assert "YouziLoadLab" in spa_response.text

    health_response = client.get("/api/health")
    assert health_response.status_code == 200
    assert health_response.headers["content-type"].startswith("application/json")
    assert health_response.json()["status"] == "ok"

    missing_api_response = client.get("/api/not-a-real-route")
    assert missing_api_response.status_code == 404
