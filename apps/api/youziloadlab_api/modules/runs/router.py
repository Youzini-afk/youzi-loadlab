from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from youziloadlab_api.db.models import Run, RunEvent, RunMetricsSnapshot
from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.run import RunCreate, RunEventRead, RunMetricsRead, RunRead
from youziloadlab_api.services.run_orchestrator import (
    ScenarioNotFoundError,
    TargetNotFoundError,
    create_run,
    list_runs,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run_endpoint(payload: RunCreate, session: Session = Depends(get_session)) -> Run:
    init_db()
    try:
        return create_run(session, payload)
    except TargetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found") from exc
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found") from exc


@router.get("", response_model=list[RunRead])
def list_runs_endpoint(session: Session = Depends(get_session)) -> list[Run]:
    init_db()
    return list_runs(session)


@router.get("/{run_id}", response_model=RunRead)
def get_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> Run:
    init_db()
    run = session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/{run_id}/events", response_model=list[RunEventRead])
def list_run_events_endpoint(run_id: str, session: Session = Depends(get_session)) -> list[RunEvent]:
    init_db()
    return list(session.exec(select(RunEvent).where(RunEvent.run_id == run_id).order_by(RunEvent.created_at)).all())


@router.get("/{run_id}/metrics", response_model=list[RunMetricsRead])
def list_run_metrics_endpoint(run_id: str, session: Session = Depends(get_session)) -> list[RunMetricsSnapshot]:
    init_db()
    return list(session.exec(select(RunMetricsSnapshot).where(RunMetricsSnapshot.run_id == run_id).order_by(RunMetricsSnapshot.timestamp)).all())
