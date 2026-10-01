from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
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

    assert saved_job is not None
    assert saved_job.company_name == "Example Company"
    assert saved_job.title == "Software Engineer"


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
