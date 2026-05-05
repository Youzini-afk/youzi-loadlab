from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import ORJSONResponse

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.session import SESSION_COOKIE_NAME, verify_session_token

PUBLIC_API_PATHS = {"/api/health", "/api/auth/login", "/api/auth/logout"}


async def require_authenticated_api(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    path = request.url.path
    if path.startswith("/api/") and path not in PUBLIC_API_PATHS:
        settings = get_settings()
        payload = verify_session_token(
            request.cookies.get(SESSION_COOKIE_NAME),
            app_secret_key=settings.app_secret_key,
        )
        if payload is None:
            return ORJSONResponse(
                {"detail": "Not authenticated"},
                status_code=401,
            )
    return await call_next(request)

