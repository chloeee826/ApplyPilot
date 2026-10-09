import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401 -- registers database models with SQLAlchemy
from app.database import create_db_and_tables
from app.routers.agent_runs import router as agent_runs_router
from app.routers.applications import router as applications_router
from app.routers.candidate_imports import router as candidate_imports_router
from app.routers.job_analyses import router as job_analyses_router
from app.routers.jobs import router as jobs_router
from app.routers.profiles import router as profiles_router
from app.routers.resume_extractions import router as resume_extractions_router


CLIENT_ROUTES = {"", "jobs", "candidate", "agent"}
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
    application.include_router(jobs_router, prefix=api_prefix)
    application.include_router(applications_router, prefix=api_prefix)
    application.include_router(profiles_router, prefix=api_prefix)
    application.include_router(job_analyses_router, prefix=api_prefix)
    application.include_router(agent_runs_router, prefix=api_prefix)
    application.include_router(resume_extractions_router, prefix=api_prefix)
    application.include_router(candidate_imports_router, prefix=api_prefix)

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
