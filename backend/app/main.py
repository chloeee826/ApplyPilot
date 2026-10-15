import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 -- registers database models with SQLAlchemy
from app.database import create_db_and_tables
from app.security import get_workspace_db
from app.routers.auth import router as auth_router
from app.routers.agent_runs import router as agent_runs_router
from app.routers.applications import router as applications_router
from app.routers.candidate_imports import router as candidate_imports_router
from app.routers.job_analyses import router as job_analyses_router
from app.routers.jobs import router as jobs_router
from app.routers.fit_checks import router as fit_checks_router
from app.routers.profiles import router as profiles_router
from app.routers.resume_extractions import router as resume_extractions_router


CLIENT_ROUTES = {"", "jobs", "candidate", "agent", "overview"}
DEFAULT_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize database tables when the API starts."""
    create_db_and_tables()
    yield


def _frontend_dist_from_environment() -> Path | None:
    serve_frontend = os.getenv("SERVE_FRONTEND", "").strip().casefold()
    if serve_frontend not in {"1", "true", "yes"}:
        return None
    return Path(os.getenv("FRONTEND_DIST_DIR", DEFAULT_FRONTEND_DIST))


def create_app(frontend_dist: Path | None = None) -> FastAPI:
    """Create the API, optionally serving a compiled React application."""
    application = FastAPI(title="ApplyPilot API", lifespan=lifespan)
    api_prefix = "/api" if frontend_dist is not None else ""

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        if request.url.path.startswith(f"{api_prefix}/auth/"):
            # Do not reflect passwords into validation-error payloads/client logs.
            errors = [{key: value for key, value in item.items() if key not in {"input", "ctx"}}
                      for item in exc.errors()]
            return JSONResponse(status_code=422, content={"detail": errors})
        return await request_validation_exception_handler(request, exc)
    application.include_router(auth_router, prefix=api_prefix)
    for router in (jobs_router, applications_router, profiles_router, job_analyses_router,
                   agent_runs_router, resume_extractions_router, candidate_imports_router, fit_checks_router):
        application.include_router(router, prefix=api_prefix, dependencies=[Depends(get_workspace_db)])

    @application.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/assets/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    @application.get("/health")
    def health_check() -> dict[str, str]:
        """Return a simple liveness response for the API."""
        return {"status": "ok"}

    if api_prefix:
        application.add_api_route(
            "/api/health",
            health_check,
            methods=["GET"],
            include_in_schema=False,
        )

    if frontend_dist is not None:
        index_file = frontend_dist / "index.html"
        assets_dir = frontend_dist / "assets"
        if not index_file.is_file() or not assets_dir.is_dir():
            raise RuntimeError(
                f"Frontend build is incomplete at {frontend_dist}. Run npm run build first."
            )

        application.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @application.get("/{client_path:path}", include_in_schema=False)
        def serve_frontend(client_path: str) -> FileResponse:
            if client_path not in CLIENT_ROUTES:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Not found",
                )
            return FileResponse(index_file)

    return application


app = create_app(_frontend_dist_from_environment())
