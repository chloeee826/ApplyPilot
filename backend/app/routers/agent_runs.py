import os
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent_run import AgentRun
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.schemas.agent_run import AgentRunCreate, AgentRunRead
from app.services.job_match_agent import (
    DEFAULT_AGENT_MODEL,
    DEMO_AGENT_MODEL,
    AgentConfigurationError,
    AgentExecutionError,
    AgentResult,
    run_demo_job_match_agent,
    run_job_match_agent,
)


router = APIRouter(prefix="/agent-runs", tags=["agent runs"])
AgentRunner = Callable[[Session, UUID, UUID], AgentResult]


def get_agent_runner() -> AgentRunner:
    """Provide the agent runner so API tests can replace the external model."""
    return run_job_match_agent


@router.post("", response_model=AgentRunRead, status_code=status.HTTP_201_CREATED)
def create_agent_run(
    request: AgentRunCreate,
    db: Annotated[Session, Depends(get_db)],
    runner: Annotated[AgentRunner, Depends(get_agent_runner)],
) -> AgentRun:
    if db.get(Job, request.job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if db.get(CandidateProfile, request.profile_id) is None:
        raise HTTPException(status_code=404, detail="Candidate profile not found")
    analysis = db.scalar(
        select(JobAnalysis).where(JobAnalysis.job_id == request.job_id)
    )
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analyze the job before running the agent",
        )

    record = AgentRun(
        job_id=request.job_id,
        profile_id=request.profile_id,
        status="running",
        model=(
            DEMO_AGENT_MODEL
            if request.mode == "demo"
            else os.getenv("OPENAI_MODEL", DEFAULT_AGENT_MODEL)
        ),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        selected_runner = run_demo_job_match_agent if request.mode == "demo" else runner
        result = selected_runner(db, request.job_id, request.profile_id)
    except (AgentConfigurationError, AgentExecutionError) as exc:
        record.status = "failed"
        record.error = str(exc)
        record.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(
            status_code=(
                status.HTTP_503_SERVICE_UNAVAILABLE
                if isinstance(exc, AgentConfigurationError)
                else status.HTTP_502_BAD_GATEWAY
            ),
            detail={"message": str(exc), "run_id": str(record.id)},
        ) from exc

    recommendation = result.recommendation
    record.status = "completed"
    record.model = result.model
    record.summary = recommendation.summary
    record.matched_skills = recommendation.matched_skills
    record.skill_gaps = recommendation.skill_gaps
    record.project_evidence = recommendation.project_evidence
    record.interview_focus = recommendation.interview_focus
    record.tool_trace = result.tool_trace
    record.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[AgentRunRead])
def list_agent_runs(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[AgentRun]:
    statement = (
        select(AgentRun)
        .order_by(AgentRun.created_at.desc(), AgentRun.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{run_id}", response_model=AgentRunRead)
def get_agent_run(
    run_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> AgentRun:
    record = db.get(AgentRun, run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return record
