from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.application import Application
from app.models.job import Job
from app.schemas.application import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationUpdate,
)


router = APIRouter(prefix="/applications", tags=["applications"])


def get_application_or_404(db: Session, application_id: UUID) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return application


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(
    application: ApplicationCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    if db.get(Job, application.job_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    existing = db.scalar(
        select(Application).where(Application.job_id == application.job_id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application already exists for this job",
        )

    record = Application(
        job_id=application.job_id,
        status=application.status.value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[ApplicationRead])
def list_applications(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Application]:
    statement = (
        select(Application)
        .order_by(Application.updated_at.desc(), Application.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.patch("/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    updates: ApplicationUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Application:
    application = get_application_or_404(db, application_id)
    application.status = updates.status.value
    db.commit()
    db.refresh(application)
    return application
