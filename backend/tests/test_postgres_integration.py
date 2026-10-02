import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.agent_run import AgentRun
from app.models.application import Application
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.routers.agent_runs import get_agent_runner
from app.services.job_match_agent import AgentResult, JobMatchRecommendation


def postgres_test_agent_runner(
    db: object,
    job_id: UUID,
    profile_id: UUID,
) -> AgentResult:
    return AgentResult(
        recommendation=JobMatchRecommendation(
            summary="Stored PostgreSQL evidence supports this candidate.",
            matched_skills=["PostgreSQL"],
            skill_gaps=["AWS"],
            project_evidence=["ApplyPilot persists structured evidence."],
            interview_focus=["Explain the persistence boundary."],
        ),
        tool_trace=[
            {
                "name": "get_job_analysis",
                "call_id": "postgres-call",
                "arguments": {},
                "output": {"skills": ["PostgreSQL"]},
            }
        ],
        model="postgres-test-model",
    )


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="Set RUN_POSTGRES_TESTS=1 to test the configured PostgreSQL database.",
)
def test_create_job_persists_in_postgres() -> None:
    app.dependency_overrides[get_agent_runner] = lambda: postgres_test_agent_runner
    with TestClient(app) as client:
        create_response = client.post(
            "/jobs",
            json={
                "company_name": "PostgreSQL Integration Test",
                "title": "Backend Engineer",
                "description": "Build PostgreSQL-backed APIs and verify persistence.",
            },
        )

        assert create_response.status_code == 201
        job_id = UUID(create_response.json()["id"])

        get_response = client.get(f"/jobs/{job_id}")
        assert get_response.status_code == 200

        list_response = client.get("/jobs")
        assert list_response.status_code == 200
        assert str(job_id) in {job["id"] for job in list_response.json()}

        update_response = client.patch(
            f"/jobs/{job_id}",
            json={"title": "Senior Backend Engineer"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Senior Backend Engineer"

        applications_response = client.get("/applications")
        assert applications_response.status_code == 200
        application = next(
            item
            for item in applications_response.json()
            if item["job_id"] == str(job_id)
        )
        assert application["status"] == "saved"

        status_response = client.patch(
            f"/applications/{application['id']}",
            json={"status": "interviewing"},
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "interviewing"

        analysis_response = client.post(f"/job-analyses/{job_id}")
        assert analysis_response.status_code == 200
        assert analysis_response.json()["parser_version"] == "rules-v1"
        assert "PostgreSQL" in analysis_response.json()["skills"]

        profile_response = client.post(
            "/profiles",
            json={
                "full_name": "PostgreSQL Test Candidate",
                "headline": "Backend Engineer",
                "summary": "Tests real persistence boundaries.",
                "skills": ["Python", "PostgreSQL"],
            },
        )
        assert profile_response.status_code == 201
        profile_id = UUID(profile_response.json()["id"])

        project_response = client.post(
            f"/profiles/{profile_id}/projects",
            json={
                "name": "ApplyPilot Integration Test",
                "description": "Verifies project evidence persistence.",
                "technologies": ["FastAPI", "SQLAlchemy"],
                "highlights": ["Persisted structured evidence in PostgreSQL."],
            },
        )
        assert project_response.status_code == 201
        project_id = UUID(project_response.json()["id"])

        projects_response = client.get(f"/profiles/{profile_id}/projects")
        assert projects_response.status_code == 200
        assert projects_response.json()[0]["id"] == str(project_id)

        agent_response = client.post(
            "/agent-runs",
            json={"job_id": str(job_id), "profile_id": str(profile_id)},
        )
        assert agent_response.status_code == 201
        agent_run_id = UUID(agent_response.json()["id"])
        assert agent_response.json()["status"] == "completed"
        assert agent_response.json()["tool_trace"][0]["name"] == "get_job_analysis"

    app.dependency_overrides.pop(get_agent_runner, None)

    with SessionLocal() as session:
        saved_job = session.get(Job, job_id)
        assert saved_job is not None
        assert saved_job.company_name == "PostgreSQL Integration Test"
        assert saved_job.title == "Senior Backend Engineer"
        saved_application = session.scalar(
            select(Application).where(Application.job_id == job_id)
        )
        assert saved_application is not None
        assert saved_application.status == "interviewing"
        saved_analysis = session.scalar(
            select(JobAnalysis).where(JobAnalysis.job_id == job_id)
        )
        assert saved_analysis is not None
        assert saved_analysis.parser_version == "rules-v1"
        saved_profile = session.get(CandidateProfile, profile_id)
        saved_project = session.get(CandidateProject, project_id)
        assert saved_profile is not None
        assert saved_profile.skills == ["Python", "PostgreSQL"]
        assert saved_project is not None
        assert saved_project.highlights == [
            "Persisted structured evidence in PostgreSQL."
        ]
        saved_agent_run = session.get(AgentRun, agent_run_id)
        assert saved_agent_run is not None
        assert saved_agent_run.model == "postgres-test-model"
        assert saved_agent_run.matched_skills == ["PostgreSQL"]

        session.delete(saved_job)
        session.delete(saved_profile)
        session.commit()
