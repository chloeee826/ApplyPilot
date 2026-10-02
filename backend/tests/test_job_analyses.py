from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.application import Application
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.services.job_parser import parse_job_description


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


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
    test_client.close()


@pytest.fixture(autouse=True)
def clear_job_data():
    with TestSessionLocal() as session:
        session.execute(delete(JobAnalysis))
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(JobAnalysis))
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()


def create_job(client: TestClient) -> dict:
    response = client.post(
        "/jobs",
        json={
            "company_name": "Parser Test Company",
            "title": "Software Engineer",
            "description": (
                "Build REST APIs using Python, FastAPI, and PostgreSQL.\n"
                "Must have 2 years of experience with SQL and Git.\n"
                "Preferred: familiarity with Docker and AWS.\n"
                "Collaborate with product teams to design reliable services."
            ),
        },
    )
    assert response.status_code == 201
    return response.json()


def test_rule_parser_extracts_structured_fields() -> None:
    parsed = parse_job_description(
        "Build APIs with Python and FastAPI. Preferred: experience with Docker."
    )

    assert parsed.skills == ["Python", "FastAPI", "Docker"]
    assert parsed.responsibilities == ["Build APIs with Python and FastAPI."]
    assert parsed.preferred_qualifications == ["Preferred: experience with Docker."]


def test_analyze_job_persists_structured_result(client: TestClient) -> None:
    job = create_job(client)

    response = client.post(f"/job-analyses/{job['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job["id"]
    assert body["parser_version"] == "rules-v1"
    assert body["skills"] == [
        "Python",
        "FastAPI",
        "SQL",
        "PostgreSQL",
        "AWS",
        "Docker",
        "Git",
        "REST APIs",
    ]
    assert len(body["requirements"]) == 1
    assert len(body["preferred_qualifications"]) == 1
    assert len(body["responsibilities"]) == 2

    with Session(test_engine) as session:
        saved_analysis = session.scalar(
            select(JobAnalysis).where(JobAnalysis.job_id == UUID(job["id"]))
        )

    assert saved_analysis is not None
    assert saved_analysis.skills == body["skills"]


def test_reanalyze_job_updates_one_existing_record(client: TestClient) -> None:
    job = create_job(client)
    first_response = client.post(f"/job-analyses/{job['id']}")
    second_response = client.post(f"/job-analyses/{job['id']}")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert len(client.get("/job-analyses").json()) == 1


def test_get_job_analysis_returns_saved_result(client: TestClient) -> None:
    job = create_job(client)
    created = client.post(f"/job-analyses/{job['id']}").json()

    response = client.get(f"/job-analyses/{job['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_job_analysis_returns_404_before_parsing(client: TestClient) -> None:
    job = create_job(client)

    response = client.get(f"/job-analyses/{job['id']}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job analysis not found"}


def test_analyze_unknown_job_returns_404(client: TestClient) -> None:
    response = client.post(
        "/job-analyses/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_changing_description_invalidates_saved_analysis(client: TestClient) -> None:
    job = create_job(client)
    client.post(f"/job-analyses/{job['id']}")

    update_response = client.patch(
        f"/jobs/{job['id']}",
        json={"description": "Develop Android applications using Java."},
    )

    assert update_response.status_code == 200
    assert client.get(f"/job-analyses/{job['id']}").status_code == 404
