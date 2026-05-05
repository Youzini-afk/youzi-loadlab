from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.modules.health.router import router as health_router
from youziloadlab_api.modules.targets.router import router as targets_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    app.include_router(targets_router, prefix="/api")
    return app


app = create_app()
