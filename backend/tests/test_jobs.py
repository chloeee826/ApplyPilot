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
def clear_jobs():
    with TestSessionLocal() as session:
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()


def test_create_job(client: TestClient) -> None:
    response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Software Engineer",
            "description": "Build reliable backend services.",
            "location": "San Francisco, CA",
            "source_url": "https://example.com/jobs/software-engineer",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["company_name"] == "Example Company"
    assert body["title"] == "Software Engineer"
    assert body["description"] == "Build reliable backend services."
    assert body["location"] == "San Francisco, CA"
    assert body["source_url"] == "https://example.com/jobs/software-engineer"
    assert body["id"]
    assert body["created_at"]

    with Session(test_engine) as session:
        saved_job = session.scalar(select(Job).where(Job.id == UUID(body["id"])))
        saved_application = session.scalar(
            select(Application).where(Application.job_id == UUID(body["id"]))
        )

    assert saved_job is not None
    assert saved_job.company_name == "Example Company"
    assert saved_job.title == "Software Engineer"
    assert saved_application is not None
    assert saved_application.status == "saved"


def test_create_job_rejects_missing_required_field(client: TestClient) -> None:
    response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "description": "This request is missing a title.",
        },
    )

    assert response.status_code == 422


def test_create_job_rejects_invalid_source_url(client: TestClient) -> None:
    response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Software Engineer",
            "description": "Build reliable backend services.",
            "source_url": "not-a-url",
        },
    )

    assert response.status_code == 422


def test_list_jobs(client: TestClient) -> None:
    for company_name in ("First Company", "Second Company"):
        response = client.post(
            "/jobs",
            json={
                "company_name": company_name,
                "title": "Software Engineer",
                "description": "Build reliable services.",
            },
        )
        assert response.status_code == 201

    response = client.get("/jobs")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert {job["company_name"] for job in response.json()} == {
        "First Company",
        "Second Company",
    }


def test_get_job(client: TestClient) -> None:
    create_response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Backend Engineer",
            "description": "Build APIs.",
        },
    )
    job_id = create_response.json()["id"]

    response = client.get(f"/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id
    assert response.json()["title"] == "Backend Engineer"


def test_get_job_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/jobs/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_update_job_changes_only_supplied_fields(client: TestClient) -> None:
    create_response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Software Engineer",
            "description": "Original description.",
            "location": "Remote",
        },
    )
    job_id = create_response.json()["id"]

    response = client.patch(
        f"/jobs/{job_id}",
        json={"title": "Senior Software Engineer", "location": None},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Senior Software Engineer"
    assert response.json()["location"] is None
    assert response.json()["description"] == "Original description."

    with Session(test_engine) as session:
        saved_job = session.get(Job, UUID(job_id))

    assert saved_job is not None
    assert saved_job.title == "Senior Software Engineer"
    assert saved_job.description == "Original description."


def test_update_job_rejects_null_required_field(client: TestClient) -> None:
    create_response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Software Engineer",
            "description": "Build reliable services.",
        },
    )
    job_id = create_response.json()["id"]

    response = client.patch(f"/jobs/{job_id}", json={"title": None})

    assert response.status_code == 422
