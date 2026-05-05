from uuid import uuid4

from fastapi.testclient import TestClient

from youziloadlab_api.main import create_app


def test_create_run_starts_in_created_state() -> None:
    client = TestClient(create_app())
    target_name = f"openai compat {uuid4()}"
    target = client.post(
        "/api/targets",
        json={
            "name": target_name,
            "kind": "openai_compatible",
            "base_url": "http://localhost:3000/",
        },
    ).json()

    response = client.post(
        "/api/runs",
        json={
            "name": "baseline chat",
            "target_id": target["id"],
            "scenario_id": "openai-chat-load",
            "config_json": {
                "request": {"model": "gpt-4o-mini"},
                "loadProfile": {"phases": []},
            },
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["name"] == "baseline chat"
    assert body["target_id"] == target["id"]
    assert body["status"] == "created"
    assert body["scenario_id"] == "openai-chat-load"
    assert body["config_json"]["request"]["model"] == "gpt-4o-mini"
    assert body["locust_web_url"] == f"/locust/{body['id']}"

    list_response = client.get("/api/runs")

    assert list_response.status_code == 200
    assert any(run["id"] == body["id"] for run in list_response.json())


def test_create_run_rejects_unknown_target() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/runs",
        json={
            "name": "missing target",
            "target_id": str(uuid4()),
            "scenario_id": "openai-chat-load",
            "config_json": {"request": {}, "loadProfile": {"phases": []}},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Target not found"


def test_create_run_rejects_unknown_scenario() -> None:
    client = TestClient(create_app())
    target_name = f"scenario target {uuid4()}"
    target = client.post(
        "/api/targets",
        json={
            "name": target_name,
            "kind": "openai_compatible",
            "base_url": "http://localhost:3000",
        },
    ).json()

    response = client.post(
        "/api/runs",
        json={
            "name": "missing scenario",
            "target_id": target["id"],
            "scenario_id": "not-a-real-scenario",
            "config_json": {"request": {}, "loadProfile": {"phases": []}},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Scenario not found"
