from sqlmodel import Session, select

from youziloadlab_api.db.models import Run, Target
from youziloadlab_api.schemas.run import RunCreate
from youziloadlab_api.services.locust_process import LocustProcessManager
from youziloadlab_api.services.scenario_registry import list_core_scenarios


class TargetNotFoundError(Exception):
    pass


class ScenarioNotFoundError(Exception):
    pass


def create_run(
    session: Session,
    payload: RunCreate,
    locust_manager: LocustProcessManager | None = None,
) -> Run:
    target = session.get(Target, payload.target_id)
    if target is None:
        raise TargetNotFoundError(payload.target_id)

    scenario_ids = {scenario["id"] for scenario in list_core_scenarios() if scenario["enabled"]}
    if payload.scenario_id not in scenario_ids:
        raise ScenarioNotFoundError(payload.scenario_id)

    run = Run(
        name=payload.name,
        target_id=payload.target_id,
        scenario_id=payload.scenario_id,
        config_json=payload.config_json,
        status="created",
    )
    launch_result = (locust_manager or LocustProcessManager()).launch_placeholder(run.id)
    run.locust_web_url = launch_result.web_url
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def list_runs(session: Session) -> list[Run]:
    return list(session.exec(select(Run).order_by(Run.created_at.desc())).all())
