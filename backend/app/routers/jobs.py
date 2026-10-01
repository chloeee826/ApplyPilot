from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead, JobUpdate


router = APIRouter(prefix="/jobs", tags=["jobs"])


def get_job_or_404(db: Session, job_id: UUID) -> Job:
    """Return a job or raise a consistent not-found response."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


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


@router.get("", response_model=list[JobRead])
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Job]:
    """Return jobs newest first with bounded pagination."""
    statement = (
        select(Job)
        .order_by(Job.created_at.desc(), Job.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    """Return one job by ID."""
    return get_job_or_404(db, job_id)


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: UUID,
    updates: JobUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Job:
    """Apply only the fields supplied by the client."""
    job = get_job_or_404(db, job_id)

    for field_name, value in updates.model_dump(
        exclude_unset=True,
        mode="json",
    ).items():
        setattr(job, field_name, value)

    db.commit()
    db.refresh(job)
    return job
