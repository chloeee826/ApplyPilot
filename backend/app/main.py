from fastapi import FastAPI

from app.routers.jobs import router as jobs_router


app = FastAPI(title="ApplyPilot API")
app.include_router(jobs_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple liveness response for the API."""
    return {"status": "ok"}
