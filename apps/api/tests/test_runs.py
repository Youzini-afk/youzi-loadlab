from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from youziloadlab_api.services.locust_process import LocustLaunchResult, LocustMetricSnapshot


class FakeLocustManager:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.exit_code: int | None = None
        self.stopped = False

    def prepare_workdir(self, run_id: str) -> Path:
        workdir = self.tmp_path / run_id
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    def write_manifest(
        self,
        *,
        run_id: str,
        scenario_id: str,
        target_base_url: str,
        config: dict[str, object],
    ) -> Path:
        workdir = self.prepare_workdir(run_id)
        manifest = workdir / "runner-config.json"
        manifest.write_text("{}", encoding="utf-8")
        return manifest

    def launch(
        self,
        *,
        run_id: str,
        scenario_id: str,
        target_base_url: str,
        config: dict[str, object],
    ) -> LocustLaunchResult:
        workdir = self.prepare_workdir(run_id)
        return LocustLaunchResult(
            web_url=f"/locust/{run_id}",
            pid=12345,
            command=["python", "-m", "locust", "--headless"],
            started=True,
            workdir=str(workdir),
            artifacts={"stats_csv": str(workdir / "locust_stats.csv")},
        )

    def get_exit_code(self, pid: int | None) -> int | None:
        return self.exit_code

    def stop(self, pid: int | None) -> bool:
        self.stopped = True
        self.exit_code = 0
        return True

    def parse_latest_metrics(self, artifacts: dict[str, object]) -> LocustMetricSnapshot:
        return LocustMetricSnapshot(
            requests_total=10,
            failures_total=1,
            current_rps=2.5,
            avg_latency_ms=120,
            p50_latency_ms=100,
            p90_latency_ms=160,
            p95_latency_ms=180,
            p99_latency_ms=240,
        )

def test_create_run_starts_in_created_state(authenticated_client: TestClient) -> None:
    client = authenticated_client
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


def test_run_start_stop_and_metrics(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_manager = FakeLocustManager(tmp_path)
    monkeypatch.setattr(
        "youziloadlab_api.services.run_orchestrator.create_default_locust_manager",
        lambda: fake_manager,
    )
    client = authenticated_client
    target = client.post(
        "/api/targets",
        json={
            "name": f"start target {uuid4()}",
            "kind": "openai_compatible",
            "base_url": "http://localhost:3000/",
        },
    ).json()
    run = client.post(
        "/api/runs",
        json={
            "name": "startable chat",
            "target_id": target["id"],
            "scenario_id": "openai-chat-load",
            "config_json": {
                "request": {"model": "gpt-4o-mini"},
                "loadProfile": {"users": 1, "spawnRate": 1, "durationSeconds": 1},
            },
        },
    ).json()

    started = client.post(f"/api/runs/{run['id']}/start")

    assert started.status_code == 200
    started_body = started.json()
    assert started_body["status"] == "running"
    assert started_body["pid"] == 12345
    assert started_body["command_json"] == ["python", "-m", "locust", "--headless"]

    fake_manager.exit_code = 0
    refreshed = client.get(f"/api/runs/{run['id']}")

    assert refreshed.status_code == 200
    assert refreshed.json()["status"] == "completed"
    metrics = client.get(f"/api/runs/{run['id']}/metrics").json()
    assert metrics[-1]["requests_total"] == 10
    assert metrics[-1]["p99_latency_ms"] == 240

    events = client.get(f"/api/runs/{run['id']}/events").json()
    assert {event["event_type"] for event in events} >= {"created", "started", "completed"}


def test_stop_running_run(
    authenticated_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fake_manager = FakeLocustManager(tmp_path)
    monkeypatch.setattr(
        "youziloadlab_api.services.run_orchestrator.create_default_locust_manager",
        lambda: fake_manager,
    )
    client = authenticated_client
    target = client.post(
        "/api/targets",
        json={
            "name": f"stop target {uuid4()}",
            "kind": "openai_compatible",
            "base_url": "http://localhost:3000/",
        },
    ).json()
    run = client.post(
        "/api/runs",
        json={
            "name": "stoppable chat",
            "target_id": target["id"],
            "scenario_id": "openai-chat-load",
            "config_json": {"request": {}, "loadProfile": {"durationSeconds": 30}},
        },
    ).json()
    assert client.post(f"/api/runs/{run['id']}/start").json()["status"] == "running"

    stopped = client.post(f"/api/runs/{run['id']}/stop")

    assert stopped.status_code == 200
    assert stopped.json()["status"] == "stopped"
    assert fake_manager.stopped is True


def test_create_run_rejects_unknown_target(authenticated_client: TestClient) -> None:
    client = authenticated_client

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


def test_create_run_rejects_unknown_scenario(authenticated_client: TestClient) -> None:
    client = authenticated_client
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
