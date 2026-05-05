from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from youziloadlab_api.db.session import get_session, init_db
from youziloadlab_api.schemas.secret import SecretCreate, SecretRead
from youziloadlab_api.services.secret_service import create_secret, list_secrets

router = APIRouter(prefix="/secrets", tags=["secrets"])


@router.post("", response_model=SecretRead, status_code=status.HTTP_201_CREATED)
def create_secret_endpoint(payload: SecretCreate, session: Session = Depends(get_session)):
    init_db()
    return create_secret(session, payload)


@router.get("", response_model=list[SecretRead])
def list_secrets_endpoint(session: Session = Depends(get_session)):
    init_db()
    return list_secrets(session)
