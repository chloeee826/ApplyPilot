from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.database import create_db_and_tables
from app import models  # noqa: F401 -- registers database models with SQLAlchemy
from app.routers.applications import router as applications_router
from app.routers.agent_runs import router as agent_runs_router
from app.routers.jobs import router as jobs_router
from app.routers.job_analyses import router as job_analyses_router
from app.routers.profiles import router as profiles_router
from app.routers.resume_extractions import router as resume_extractions_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize database tables when the API starts."""
    create_db_and_tables()
    yield


app = FastAPI(title="ApplyPilot API", lifespan=lifespan)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(profiles_router)
app.include_router(job_analyses_router)
app.include_router(agent_runs_router)
app.include_router(resume_extractions_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple liveness response for the API."""
    return {"status": "ok"}
