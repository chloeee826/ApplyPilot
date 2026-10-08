from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.application import Application
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from scripts.seed_demo import DEMO_COMPANY, DEMO_PROFILE_NAME, seed_demo_data


def test_seed_demo_data_is_complete_and_idempotent() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        first = seed_demo_data(session)
        second = seed_demo_data(session)

        assert second == first
        assert session.scalar(select(func.count()).select_from(Job)) == 1
        assert session.scalar(select(func.count()).select_from(Application)) == 1
        assert session.scalar(select(func.count()).select_from(JobAnalysis)) == 1
        assert session.scalar(select(func.count()).select_from(CandidateProfile)) == 1
        assert session.scalar(select(func.count()).select_from(CandidateProject)) == 1

        job = session.get(Job, first.job_id)
        profile = session.get(CandidateProfile, first.profile_id)
        analysis = session.get(JobAnalysis, first.analysis_id)
        assert job is not None and job.company_name == DEMO_COMPANY
        assert profile is not None and profile.full_name == DEMO_PROFILE_NAME
        assert analysis is not None and "Docker" in analysis.skills

    engine.dispose()
