"""One explicit, no-cost action from reviewed evidence and a JD to a saved report."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import current_owner, owned
from app.models.agent_run import AgentRun
from app.models.application import Application
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.routers.agent_runs import read_run
from app.schemas.agent_run import AgentRunRead
from app.schemas.application import ApplicationRead
from app.schemas.job import JobCreate, JobRead
from app.schemas.job_analysis import JobAnalysisRead
from app.services.job_match_agent import run_demo_job_match_agent
from app.services.job_parser import PARSER_VERSION, parse_job_description

router = APIRouter(prefix="/fit-checks", tags=["guided fit checks"])


class FitCheckCreate(BaseModel):
    request_id: UUID
    profile_id: UUID
    job: JobCreate


class FitCheckRead(BaseModel):
    job: JobRead
    application: ApplicationRead
    analysis: JobAnalysisRead
    report: AgentRunRead


@router.post("", response_model=FitCheckRead)
def check_fit(request: FitCheckCreate, db: Annotated[Session, Depends(get_db)]) -> FitCheckRead:
    if owned(db, CandidateProfile, request.profile_id) is None:
        raise HTTPException(404, "Save a reviewed candidate profile first.")
    values = request.job.model_dump(mode="json")
    job = db.get(Job, request.request_id)
    if job is not None:
        owned(db, Job, job.id)
        if any(getattr(job, key) != value for key, value in values.items()):
            raise HTTPException(409, "This check has different inputs. Start a new check.")
        record = db.scalar(select(AgentRun).where(AgentRun.job_id == job.id).order_by(AgentRun.created_at, AgentRun.id))
        application = db.scalar(select(Application).where(Application.job_id == job.id))
        analysis = db.scalar(select(JobAnalysis).where(JobAnalysis.job_id == job.id))
        if record is None or application is None or analysis is None or record.profile_id != request.profile_id:
            raise HTTPException(409, "This check is unavailable. Start a new check.")
        report = read_run(db, record)
        if report.context_status != "unchanged":
            raise HTTPException(409, "Your evidence changed. Start a new check to use it.")
        return FitCheckRead(job=job, application=application, analysis=analysis, report=report)

    # One transaction: a failed check leaves no partial job/application/report.
    # The client-generated job UUID makes response-loss retries idempotent.
    try:
        job = Job(id=request.request_id, owner_id=current_owner(db), **values)
        db.add(job)
        db.flush()
        application = Application(job_id=job.id, status="saved")
        parsed = parse_job_description(job.description)  # Never calls a paid API.
        analysis = JobAnalysis(job_id=job.id, parser_version=PARSER_VERSION, **vars(parsed))
        db.add_all([application, analysis])
        db.flush()
        result = run_demo_job_match_agent(db, job.id, request.profile_id)
        record = AgentRun(
            job_id=job.id, profile_id=request.profile_id, status="completed", model=result.model,
            **result.recommendation.model_dump(), tool_trace=result.tool_trace,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "This check may already be saved. Retry the same check.") from exc
    except Exception:
        db.rollback()
        raise
    return FitCheckRead(job=job, application=application, analysis=analysis, report=read_run(db, record))
