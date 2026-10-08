from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, create_db_and_tables
from app.models.application import Application
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.services.job_parser import PARSER_VERSION, parse_job_description


DEMO_COMPANY = "ApplyPilot Demo Co"
DEMO_ROLE = "Applied AI Engineer"
DEMO_PROFILE_NAME = "Demo Candidate"
DEMO_PROJECT_NAME = "ApplyPilot"

DEMO_JOB_DESCRIPTION = """Build production AI applications using Python, FastAPI,
PostgreSQL, React, TypeScript, and REST APIs. Design reliable backend services and
evidence-grounded agent workflows. Experience with Docker is required. Preferred:
experience evaluating LLM applications."""


@dataclass(frozen=True)
class SeedResult:
    job_id: UUID
    profile_id: UUID
    project_id: UUID
    analysis_id: UUID


def seed_demo_data(db: Session) -> SeedResult:
    """Create or refresh one complete, repeatable local demo workspace."""
    job = db.scalar(
        select(Job).where(
            Job.company_name == DEMO_COMPANY,
            Job.title == DEMO_ROLE,
        )
    )
    if job is None:
        job = Job(
            company_name=DEMO_COMPANY,
            title=DEMO_ROLE,
            description=DEMO_JOB_DESCRIPTION,
            location="Remote",
        )
        db.add(job)
        db.flush()
    else:
        job.description = DEMO_JOB_DESCRIPTION
        job.location = "Remote"

    application = db.scalar(
        select(Application).where(Application.job_id == job.id)
    )
    if application is None:
        db.add(Application(job_id=job.id, status="saved"))

    parsed = parse_job_description(DEMO_JOB_DESCRIPTION)
    analysis_values = {
        "skills": parsed.skills,
        "requirements": parsed.requirements,
        "preferred_qualifications": parsed.preferred_qualifications,
        "responsibilities": parsed.responsibilities,
        "parser_version": PARSER_VERSION,
    }
    analysis = db.scalar(select(JobAnalysis).where(JobAnalysis.job_id == job.id))
    if analysis is None:
        analysis = JobAnalysis(job_id=job.id, **analysis_values)
        db.add(analysis)
    else:
        for field_name, value in analysis_values.items():
            setattr(analysis, field_name, value)

    profile = db.scalar(
        select(CandidateProfile).where(
            CandidateProfile.full_name == DEMO_PROFILE_NAME
        )
    )
    profile_values = {
        "headline": "Software Engineer building reliable AI products",
        "summary": (
            "Full-stack engineer experienced in Python APIs, React applications, "
            "relational data modeling, and evidence-grounded AI workflows."
        ),
        "skills": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "React",
            "TypeScript",
            "REST APIs",
            "Automated Testing",
        ],
    }
    if profile is None:
        profile = CandidateProfile(full_name=DEMO_PROFILE_NAME, **profile_values)
        db.add(profile)
        db.flush()
    else:
        for field_name, value in profile_values.items():
            setattr(profile, field_name, value)

    project = db.scalar(
        select(CandidateProject).where(
            CandidateProject.profile_id == profile.id,
            CandidateProject.name == DEMO_PROJECT_NAME,
        )
    )
    project_values = {
        "description": (
            "An agentic job-search platform that grounds recommendations in stored "
            "job and candidate evidence."
        ),
        "technologies": [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "React",
            "TypeScript",
            "OpenAI API",
        ],
        "highlights": [
            "Implemented four controlled evidence-retrieval tools with required-tool validation.",
            "Persisted completed and failed agent runs with inspectable tool traces.",
            "Validated backend workflows with PostgreSQL integration tests.",
        ],
    }
    if project is None:
        project = CandidateProject(
            profile_id=profile.id,
            name=DEMO_PROJECT_NAME,
            **project_values,
        )
        db.add(project)
    else:
        for field_name, value in project_values.items():
            setattr(project, field_name, value)

    db.commit()
    db.refresh(job)
    db.refresh(profile)
    db.refresh(project)
    db.refresh(analysis)
    return SeedResult(
        job_id=job.id,
        profile_id=profile.id,
        project_id=project.id,
        analysis_id=analysis.id,
    )


def main() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        result = seed_demo_data(session)

    print("ApplyPilot demo data is ready.")
    print(f"job_id={result.job_id}")
    print(f"profile_id={result.profile_id}")
    print("Next: open http://127.0.0.1:5173/agent and run Deterministic demo.")


if __name__ == "__main__":
    main()
