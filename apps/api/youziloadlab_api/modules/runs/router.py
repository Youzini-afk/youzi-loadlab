from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.run import RunCreate, RunRead
from youziloadlab_api.services.run_orchestrator import (
    ScenarioNotFoundError,
    TargetNotFoundError,
    create_run,
    list_runs,
)

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run_endpoint(payload: RunCreate, session: Session = Depends(get_session)):
    init_db()
    try:
        return create_run(session, payload)
    except TargetNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found") from exc
    except ScenarioNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found") from exc


@router.get("", response_model=list[RunRead])
def list_runs_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_runs(session)
