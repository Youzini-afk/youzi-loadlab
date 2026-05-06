from uuid import uuid4

from fastapi.testclient import TestClient

from youziloadlab_api.services.report_service import evaluate_basic_thresholds, render_markdown_report


def test_render_markdown_report_contains_summary_and_redacts_secrets() -> None:
    markdown = render_markdown_report(
        run_name="baseline",
        scenario_id="openai-chat-load",
        summary={"requests_total": 10, "failures_total": 1, "p95_latency_ms": 123.4},
        notes="Authorization: Bearer sk-secret123",
    )

    assert "# YouziLoadLab Run Report" in markdown
    assert "baseline" in markdown
    assert "openai-chat-load" in markdown
    assert "requests_total" in markdown
    assert "sk-secret123" not in markdown
    assert "[REDACTED_BEARER]" in markdown


def test_evaluate_basic_thresholds_fails_low_success_or_high_p99() -> None:
    result = evaluate_basic_thresholds(
        requests_total=100,
        failures_total=10,
        p99_latency_ms=12000,
    )

    assert result["status"] == "fail"
    assert "Success rate is below 95%." in result["reasons"]
    assert "P99 latency is above 10 seconds." in result["reasons"]


def test_report_api_builds_report_for_run(authenticated_client: TestClient) -> None:
    client = authenticated_client
    target = client.post(
        "/api/targets",
        json={
            "name": f"report target {uuid4()}",
            "kind": "openai_compatible",
            "base_url": "http://localhost:3000/",
        },
    ).json()
    run = client.post(
        "/api/runs",
        json={
            "name": "reportable chat",
            "target_id": target["id"],
            "scenario_id": "openai-chat-load",
            "config_json": {"request": {}, "loadProfile": {"durationSeconds": 1}},
        },
    ).json()

    response = client.post(f"/api/reports/run/{run['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == run["id"]
    assert body["summary_json"]["run"]["status"] == "created"
    assert "# YouziLoadLab Run Report" in body["markdown"]
