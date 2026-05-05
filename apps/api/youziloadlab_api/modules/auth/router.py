import secrets

from fastapi import APIRouter, HTTPException, Response, status

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.session import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
)
from youziloadlab_api.schemas.auth import AuthStatus, AuthUser, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthStatus)
def login(payload: LoginRequest, response: Response) -> AuthStatus:
    settings = get_settings()
    if not secrets.compare_digest(payload.password, settings.admin_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    token = create_session_token(app_secret_key=settings.app_secret_key)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        path="/",
    )
    return AuthStatus(authenticated=True, user=AuthUser(username="admin"))


@router.post("/logout", response_model=AuthStatus)
def logout(response: Response) -> AuthStatus:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return AuthStatus(authenticated=False, user=None)


@router.get("/me", response_model=AuthStatus)
def me() -> AuthStatus:
    return AuthStatus(authenticated=True, user=AuthUser(username="admin"))

