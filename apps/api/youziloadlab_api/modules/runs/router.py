from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from youziloadlab_api.db.models import Run, RunEvent, RunMetricsSnapshot
from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.run import RunCreate, RunEventRead, RunMetricsRead, RunRead
from youziloadlab_api.services.run_orchestrator import (
    RunNotFoundError,
    RunStateError,
    ScenarioNotFoundError,
    TargetNotFoundError,
    create_run,
    get_run_or_raise,
    list_runs,
    start_run,
    stop_run,
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
    try:
        return get_run_or_raise(session, run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc


@router.post("/{run_id}/start", response_model=RunRead)
def start_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> Run:
    init_db()
    try:
        return start_run(session, run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc
    except TargetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found") from exc
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found") from exc
    except RunStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{run_id}/stop", response_model=RunRead)
def stop_run_endpoint(run_id: str, session: Session = Depends(get_session)) -> Run:
    init_db()
    try:
        return stop_run(session, run_id)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found") from exc


@router.get("/{run_id}/events", response_model=list[RunEventRead])
def list_run_events_endpoint(run_id: str, session: Session = Depends(get_session)) -> list[RunEvent]:
    init_db()
    return list(
        session.exec(
            select(RunEvent)
            .where(RunEvent.run_id == run_id)
            .order_by(cast(Any, RunEvent.created_at))
        ).all()
    )


@router.get("/{run_id}/metrics", response_model=list[RunMetricsRead])
def list_run_metrics_endpoint(run_id: str, session: Session = Depends(get_session)) -> list[RunMetricsSnapshot]:
    init_db()
    return list(
        session.exec(
            select(RunMetricsSnapshot)
            .where(RunMetricsSnapshot.run_id == run_id)
            .order_by(cast(Any, RunMetricsSnapshot.timestamp))
        ).all()
    )
