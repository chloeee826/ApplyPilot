from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead


router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(
    job: JobCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    """Validate and persist a job in the configured database."""
    job_record = Job(**job.model_dump(mode="json"))
    db.add(job_record)
    db.commit()
    db.refresh(job_record)
    return job_record
