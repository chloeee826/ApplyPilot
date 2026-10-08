from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.agent_run import AgentRun
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.routers.agent_runs import get_agent_runner
from app.services.job_match_agent import (
    AgentExecutionError,
    AgentResult,
    JobMatchRecommendation,
)


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    with TestSessionLocal() as session:
        yield session


def successful_runner(db: Session, job_id: UUID, profile_id: UUID) -> AgentResult:
    assert db.get(Job, job_id) is not None
    assert db.get(CandidateProfile, profile_id) is not None
    return AgentResult(
        recommendation=JobMatchRecommendation(
            summary="The candidate has relevant backend evidence.",
            matched_skills=["Python", "FastAPI"],
            skill_gaps=["AWS"],
            project_evidence=["ApplyPilot uses FastAPI and PostgreSQL."],
            interview_focus=["Prepare an API design deep dive."],
        ),
        tool_trace=[
            {
                "name": "get_job",
                "call_id": "call-1",
                "arguments": {},
                "output": {"title": "Backend Engineer"},
            }
        ],
        model="fake-agent-model",
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_agent_runner] = lambda: successful_runner
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
    test_client.close()


@pytest.fixture(autouse=True)
def clear_agent_data():
    with TestSessionLocal() as session:
        session.execute(delete(AgentRun))
        session.execute(delete(JobAnalysis))
        session.execute(delete(CandidateProject))
        session.execute(delete(CandidateProfile))
        session.execute(delete(Job))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(AgentRun))
        session.execute(delete(JobAnalysis))
        session.execute(delete(CandidateProject))
        session.execute(delete(CandidateProfile))
        session.execute(delete(Job))
        session.commit()


def create_agent_context(client: TestClient, *, analyze: bool = True) -> tuple[dict, dict]:
    job_response = client.post(
        "/jobs",
        json={
            "company_name": "Example Co",
            "title": "Backend Engineer",
            "description": "Build Python and FastAPI services. Preferred: AWS.",
        },
    )
    profile_response = client.post(
        "/profiles",
        json={
            "full_name": "Chloe Example",
            "headline": "Software Engineer",
            "summary": "Builds reliable products.",
            "skills": ["Python", "FastAPI"],
        },
    )
    assert job_response.status_code == 201
    assert profile_response.status_code == 201
    job = job_response.json()
    profile = profile_response.json()
    if analyze:
        assert client.post(f"/job-analyses/{job['id']}").status_code == 200
    return job, profile


def test_create_agent_run_persists_recommendation(client: TestClient) -> None:
    job, profile = create_agent_context(client)

    response = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["model"] == "fake-agent-model"
    assert body["matched_skills"] == ["Python", "FastAPI"]
    assert body["skill_gaps"] == ["AWS"]
    assert body["tool_trace"][0]["name"] == "get_job"
    assert body["completed_at"] is not None

    with Session(test_engine) as session:
        saved = session.get(AgentRun, UUID(body["id"]))
    assert saved is not None
    assert saved.summary == "The candidate has relevant backend evidence."


def test_demo_agent_run_completes_without_external_model(client: TestClient) -> None:
    job, profile = create_agent_context(client)

    response = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"], "mode": "demo"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["model"] == "demo-evidence-v1"
    assert [item["name"] for item in body["tool_trace"]] == [
        "get_job",
        "get_job_analysis",
        "get_candidate_profile",
        "list_candidate_projects",
    ]
    assert body["summary"].startswith("Stored evidence supports")

    with Session(test_engine) as session:
        saved = session.get(AgentRun, UUID(body["id"]))
    assert saved is not None
    assert saved.status == "completed"
    assert saved.model == "demo-evidence-v1"


def test_agent_run_rejects_unknown_execution_mode(client: TestClient) -> None:
    job, profile = create_agent_context(client)

    response = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"], "mode": "pretend"},
    )

    assert response.status_code == 422


def test_list_and_get_agent_runs(client: TestClient) -> None:
    job, profile = create_agent_context(client)
    created = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"]},
    ).json()

    list_response = client.get("/agent-runs")
    get_response = client.get(f"/agent-runs/{created['id']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == created["id"]
    assert get_response.status_code == 200
    assert get_response.json()["project_evidence"] == [
        "ApplyPilot uses FastAPI and PostgreSQL."
    ]


def test_agent_requires_saved_job_analysis(client: TestClient) -> None:
    job, profile = create_agent_context(client, analyze=False)

    response = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"]},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Analyze the job before running the agent"}


def test_failed_agent_run_is_persisted(client: TestClient) -> None:
    job, profile = create_agent_context(client)

    def failing_runner(db: Session, job_id: UUID, profile_id: UUID) -> AgentResult:
        raise AgentExecutionError("Model response was incomplete")

    app.dependency_overrides[get_agent_runner] = lambda: failing_runner
    response = client.post(
        "/agent-runs",
        json={"job_id": job["id"], "profile_id": profile["id"]},
    )

    assert response.status_code == 502
    run_id = response.json()["detail"]["run_id"]
    saved = client.get(f"/agent-runs/{run_id}")
    assert saved.status_code == 200
    assert saved.json()["status"] == "failed"
    assert saved.json()["error"] == "Model response was incomplete"
