from fastapi import APIRouter

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.core.time import utc_now_iso

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
        "timestamp": utc_now_iso(),
    }
