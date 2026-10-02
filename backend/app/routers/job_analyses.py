from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.schemas.job_analysis import JobAnalysisRead
from app.services.job_parser import PARSER_VERSION, parse_job_description


router = APIRouter(prefix="/job-analyses", tags=["job analyses"])


def get_job_or_404(db: Session, job_id: UUID) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.get("", response_model=list[JobAnalysisRead])
def list_job_analyses(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[JobAnalysis]:
    statement = (
        select(JobAnalysis)
        .order_by(JobAnalysis.updated_at.desc(), JobAnalysis.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{job_id}", response_model=JobAnalysisRead)
def get_job_analysis(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> JobAnalysis:
    get_job_or_404(db, job_id)
    analysis = db.scalar(select(JobAnalysis).where(JobAnalysis.job_id == job_id))
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job analysis not found",
        )
    return analysis


@router.post("/{job_id}", response_model=JobAnalysisRead)
def analyze_job(
    job_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> JobAnalysis:
    job = get_job_or_404(db, job_id)
    parsed = parse_job_description(job.description)
    values = {
        "skills": parsed.skills,
        "requirements": parsed.requirements,
        "preferred_qualifications": parsed.preferred_qualifications,
        "responsibilities": parsed.responsibilities,
        "parser_version": PARSER_VERSION,
    }

    analysis = db.scalar(select(JobAnalysis).where(JobAnalysis.job_id == job_id))
    if analysis is None:
        analysis = JobAnalysis(job_id=job_id, **values)
        db.add(analysis)
    else:
        for field_name, value in values.items():
            setattr(analysis, field_name, value)

    db.commit()
    db.refresh(analysis)
    return analysis
