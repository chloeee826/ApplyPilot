from fastapi import FastAPI


app = FastAPI(title="ApplyPilot API")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return a simple liveness response for the API."""
    return {"status": "ok"}
