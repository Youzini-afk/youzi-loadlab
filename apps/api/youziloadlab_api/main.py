from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from youziloadlab_api.core.config import get_settings
from youziloadlab_api.middleware.auth import require_authenticated_api
from youziloadlab_api.modules.auth.router import router as auth_router
from youziloadlab_api.modules.health.router import router as health_router
from youziloadlab_api.modules.reports.router import router as reports_router
from youziloadlab_api.modules.runs.router import router as runs_router
from youziloadlab_api.modules.scenarios.router import router as scenarios_router
from youziloadlab_api.modules.secrets.router import router as secrets_router
from youziloadlab_api.modules.targets.router import router as targets_router

DEFAULT_STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(static_dir: Path | str | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(require_authenticated_api)
    app.include_router(auth_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    app.include_router(reports_router, prefix="/api")
    app.include_router(runs_router, prefix="/api")
    app.include_router(scenarios_router, prefix="/api")
    app.include_router(secrets_router, prefix="/api")
    app.include_router(targets_router, prefix="/api")
    mount_static_web(app, static_dir=static_dir)
    return app


def mount_static_web(app: FastAPI, static_dir: Path | str | None = None) -> None:
    resolved_static_dir = Path(static_dir) if static_dir is not None else DEFAULT_STATIC_DIR
    index_path = resolved_static_dir / "index.html"
    if not index_path.is_file():
        return

    static_root = resolved_static_dir.resolve()

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str) -> FileResponse:
        if full_path == "" or full_path == "/":
            return FileResponse(index_path)
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        requested_path = (static_root / full_path).resolve()
        try:
            requested_path.relative_to(static_root)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Not Found") from exc

        if requested_path.is_file():
            return FileResponse(requested_path)
        return FileResponse(index_path)


app = create_app()
