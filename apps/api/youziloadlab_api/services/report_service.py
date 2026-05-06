import json
from pathlib import Path
from typing import Any, cast

from sqlmodel import Session, select

from youziloadlab_api.core.security import redact_sensitive_text
from youziloadlab_api.core.time import utc_now_iso
from youziloadlab_api.db.models import Report, Run, RunEvent, RunMetricsSnapshot


def build_run_summary(
    *,
    run: Run,
    metrics: list[RunMetricsSnapshot],
    events: list[RunEvent],
    notes: str = "",
) -> dict[str, Any]:
    latest_metric = metrics[-1] if metrics else None
    requests_total = latest_metric.requests_total if latest_metric else 0
    failures_total = latest_metric.failures_total if latest_metric else 0
    success_rate = (
        (requests_total - failures_total) / requests_total if requests_total > 0 else None
    )
    threshold = evaluate_basic_thresholds(
        requests_total=requests_total,
        failures_total=failures_total,
        p99_latency_ms=latest_metric.p99_latency_ms if latest_metric else 0,
    )
    return {
        "run": {
            "id": run.id,
            "name": run.name,
            "scenarioId": run.scenario_id,
            "status": run.status,
            "startedAt": run.started_at.isoformat() if run.started_at else None,
            "finishedAt": run.finished_at.isoformat() if run.finished_at else None,
            "exitCode": run.exit_code,
            "errorMessage": run.error_message,
        },
        "metrics": {
            "requestsTotal": requests_total,
            "failuresTotal": failures_total,
            "successRate": success_rate,
            "currentRps": latest_metric.current_rps if latest_metric else 0,
            "avgLatencyMs": latest_metric.avg_latency_ms if latest_metric else 0,
            "p50LatencyMs": latest_metric.p50_latency_ms if latest_metric else 0,
            "p90LatencyMs": latest_metric.p90_latency_ms if latest_metric else 0,
            "p95LatencyMs": latest_metric.p95_latency_ms if latest_metric else 0,
            "p99LatencyMs": latest_metric.p99_latency_ms if latest_metric else 0,
        },
        "threshold": threshold,
        "artifacts": run.artifacts_json,
        "events": {
            "count": len(events),
            "types": sorted({event.event_type for event in events}),
        },
        "security": run.config_json.get("securityFindings", []),
        "cleanup": run.config_json.get("cleanupStatus", {"status": "unknown"}),
        "notes": redact_sensitive_text(notes),
    }


def evaluate_basic_thresholds(
    *,
    requests_total: int,
    failures_total: int,
    p99_latency_ms: float,
) -> dict[str, Any]:
    if requests_total <= 0:
        return {
            "status": "unknown",
            "reasons": ["No request metrics were collected."],
        }
    success_rate = (requests_total - failures_total) / requests_total
    reasons: list[str] = []
    status = "pass"
    if success_rate < 0.95:
        status = "fail"
        reasons.append("Success rate is below 95%.")
    if p99_latency_ms > 10000:
        status = "fail"
        reasons.append("P99 latency is above 10 seconds.")
    if not reasons:
        reasons.append("Basic success-rate and P99 thresholds passed.")
    return {
        "status": status,
        "successRate": success_rate,
        "p99LatencyMs": p99_latency_ms,
        "reasons": reasons,
    }


def render_markdown_report(
    *,
    run_name: str,
    scenario_id: str,
    summary: dict[str, Any],
    notes: str,
) -> str:
    safe_summary = redact_sensitive_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    safe_notes = redact_sensitive_text(notes)
    return f"""# YouziLoadLab Run Report

Generated at: {utc_now_iso()}

## Run

- Name: {run_name}
- Scenario: {scenario_id}

## Summary

```json
{safe_summary}
```

## Notes

{safe_notes}
"""


def build_or_update_report(session: Session, *, run_id: str, notes: str = "") -> Report:
    run = session.get(Run, run_id)
    if run is None:
        raise ValueError("Run not found")
    metrics = list(
        session.exec(
            select(RunMetricsSnapshot)
            .where(RunMetricsSnapshot.run_id == run_id)
            .order_by(cast(Any, RunMetricsSnapshot.timestamp))
        ).all()
    )
    events = list(
        session.exec(
            select(RunEvent)
            .where(RunEvent.run_id == run_id)
            .order_by(cast(Any, RunEvent.created_at))
        ).all()
    )
    summary = build_run_summary(run=run, metrics=metrics, events=events, notes=notes)
    markdown = render_markdown_report(
        run_name=run.name,
        scenario_id=run.scenario_id,
        summary=summary,
        notes=notes,
    )
    existing = session.exec(select(Report).where(Report.run_id == run_id)).first()
    if existing is None:
        report = Report(run_id=run_id, summary_json=summary, markdown=markdown)
    else:
        report = existing
        report.summary_json = summary
        report.markdown = markdown
    session.add(report)
    session.commit()
    session.refresh(report)
    write_report_artifacts(run=run, summary=summary, markdown=markdown)
    return report


def write_report_artifacts(*, run: Run, summary: dict[str, Any], markdown: str) -> None:
    if not run.workdir:
        return
    workdir = Path(run.workdir)
    if not workdir.is_dir():
        return
    (workdir / "report.json").write_text(
        redact_sensitive_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)),
        encoding="utf-8",
    )
    (workdir / "report.md").write_text(redact_sensitive_text(markdown), encoding="utf-8")
