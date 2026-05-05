from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.target import TargetCreate, TargetRead
from youziloadlab_api.services.target_service import create_target, list_targets

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target_endpoint(payload: TargetCreate, session: Session = Depends(get_session)):
    init_db()
    return create_target(session, payload)


@router.get("", response_model=list[TargetRead])
def list_targets_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_targets(session)
