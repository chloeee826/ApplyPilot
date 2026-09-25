from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status

from app.schemas.job import JobCreate, JobRead


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(job: JobCreate) -> JobRead:
    """Validate and create a job in the current application process."""
    return JobRead(
        **job.model_dump(),
        id=uuid4(),
        created_at=datetime.now(timezone.utc),
    )
