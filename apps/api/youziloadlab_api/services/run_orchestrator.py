from typing import Any, cast

from sqlmodel import Session, select

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.security import redact_sensitive_text
from youziloadlab_api.core.time import utc_now
from youziloadlab_api.db.models import Run, RunEvent, RunMetricsSnapshot, Target
from youziloadlab_api.schemas.run import RunCreate
from youziloadlab_api.services.locust_process import LocustProcessManager
from youziloadlab_api.services.scenario_registry import list_core_scenarios


TERMINAL_RUN_STATUSES = {"completed", "failed", "stopped"}


class TargetNotFoundError(Exception):
    pass


class ScenarioNotFoundError(Exception):
    pass


class RunNotFoundError(Exception):
    pass


class RunStateError(Exception):
    pass


def create_run(
    session: Session,
    payload: RunCreate,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    target = session.get(Target, payload.target_id)
    if target is None:
        raise TargetNotFoundError(payload.target_id)

    if payload.scenario_id not in enabled_scenario_ids():
        raise ScenarioNotFoundError(payload.scenario_id)

    manager = locust_manager or create_default_locust_manager()
    run = Run(
        name=payload.name,
        target_id=payload.target_id,
        scenario_id=payload.scenario_id,
        config_json=payload.config_json,
        status="created",
    )
    workdir = manager.prepare_workdir(run.id)
    manager.write_manifest(
        run_id=run.id,
        scenario_id=run.scenario_id,
        target_base_url=target.base_url,
        config=run.config_json,
    )
    run.workdir = str(workdir)
    run.locust_web_url = f"/locust/{run.id}"
    run.artifacts_json = {"manifest": str(workdir / "runner-config.json")}
    session.add(run)
    session.commit()
    session.refresh(run)
    add_run_event(
        session,
        run_id=run.id,
        event_type="created",
        message="Run created and manifest prepared.",
        payload={"workdir": run.workdir},
    )
    return run


def start_run(
    session: Session,
    run_id: str,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    run = get_run_or_raise(session, run_id)
    refresh_run_status(session, run, locust_manager=locust_manager)
    if run.status in {"running", "preparing", "stopping"}:
        raise RunStateError(f"Run is already {run.status}")
    if run.status in TERMINAL_RUN_STATUSES:
        raise RunStateError(f"Run is already terminal: {run.status}")
    target = session.get(Target, run.target_id)
    if target is None:
        raise TargetNotFoundError(run.target_id)
    if run.scenario_id not in enabled_scenario_ids():
        raise ScenarioNotFoundError(run.scenario_id)

    manager = locust_manager or create_default_locust_manager()
    run.status = "preparing"
    session.add(run)
    session.commit()
    add_run_event(session, run_id=run.id, event_type="preparing", message="Preparing Locust process.")
    try:
        launch_result = manager.launch(
            run_id=run.id,
            scenario_id=run.scenario_id,
            target_base_url=target.base_url,
            config=run.config_json,
        )
    except Exception as exc:
        run.status = "failed"
        run.error_message = redact_sensitive_text(str(exc))
        run.finished_at = utc_now()
        session.add(run)
        session.commit()
        add_run_event(
            session,
            run_id=run.id,
            level="error",
            event_type="failed_to_start",
            message=run.error_message,
        )
        return run

    run.status = "running"
    run.pid = launch_result.pid
    run.locust_web_url = launch_result.web_url
    run.command_json = launch_result.command
    run.workdir = launch_result.workdir
    run.artifacts_json = launch_result.artifacts
    run.started_at = utc_now()
    run.error_message = None
    session.add(run)
    session.commit()
    session.refresh(run)
    add_run_event(
        session,
        run_id=run.id,
        event_type="started",
        message="Locust process started.",
        payload={
            "pid": run.pid,
            "command": run.command_json,
            "artifacts": run.artifacts_json,
        },
    )
    return run


def stop_run(
    session: Session,
    run_id: str,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    run = get_run_or_raise(session, run_id)
    refresh_run_status(session, run, locust_manager=locust_manager)
    if run.status in TERMINAL_RUN_STATUSES:
        return run
    manager = locust_manager or create_default_locust_manager()
    run.status = "stopping"
    session.add(run)
    session.commit()
    stopped = manager.stop(run.pid)
    run.status = "stopped"
    run.finished_at = utc_now()
    session.add(run)
    session.commit()
    add_run_event(
        session,
        run_id=run.id,
        event_type="stopped",
        message="Locust process stopped." if stopped else "Run marked stopped; process was not found.",
        payload={"pid": run.pid, "process_found": stopped},
    )
    session.refresh(run)
    return run


def refresh_run_status(
    session: Session,
    run: Run,
    *,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    if run.status not in {"running", "stopping"}:
        return run
    manager = locust_manager or create_default_locust_manager()
    snapshot = manager.parse_latest_metrics(run.artifacts_json)
    if snapshot is not None:
        session.add(
            RunMetricsSnapshot(
                run_id=run.id,
                requests_total=snapshot.requests_total,
                failures_total=snapshot.failures_total,
                current_rps=snapshot.current_rps,
                avg_latency_ms=snapshot.avg_latency_ms,
                p50_latency_ms=snapshot.p50_latency_ms,
                p90_latency_ms=snapshot.p90_latency_ms,
                p95_latency_ms=snapshot.p95_latency_ms,
                p99_latency_ms=snapshot.p99_latency_ms,
            )
        )
        session.commit()
    exit_code = manager.get_exit_code(run.pid)
    if exit_code is None:
        return run

    run.exit_code = exit_code
    run.finished_at = utc_now()
    if run.status == "stopping":
        run.status = "stopped"
    elif exit_code == 0:
        run.status = "completed"
    else:
        run.status = "failed"
        run.error_message = f"Locust exited with code {exit_code}"
    session.add(run)
    session.commit()
    add_run_event(
        session,
        run_id=run.id,
        level="error" if run.status == "failed" else "info",
        event_type=run.status,
        message=run.error_message or f"Run {run.status}.",
        payload={"exit_code": exit_code},
    )
    session.refresh(run)
    return run


def list_runs(
    session: Session,
    locust_manager: LocustProcessManager | None = None,
) -> list[Run]:
    runs = list(session.exec(select(Run).order_by(cast(Any, Run.created_at).desc())).all())
    for run in runs:
        refresh_run_status(session, run, locust_manager=locust_manager)
    return runs


def get_run_or_raise(
    session: Session,
    run_id: str,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    run = session.get(Run, run_id)
    if run is None:
        raise RunNotFoundError(run_id)
    return refresh_run_status(session, run, locust_manager=locust_manager)


def add_run_event(
    session: Session,
    *,
    run_id: str,
    event_type: str,
    message: str,
    level: str = "info",
    payload: dict[str, Any] | None = None,
) -> RunEvent:
    event = RunEvent(
        run_id=run_id,
        level=level,
        event_type=event_type,
        message=redact_sensitive_text(message),
        payload_json=payload or {},
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def enabled_scenario_ids() -> set[str]:
    return {scenario["id"] for scenario in list_core_scenarios() if scenario["enabled"]}


def create_default_locust_manager() -> LocustProcessManager:
    return LocustProcessManager(runner_workdir=get_settings().runner_workdir)
