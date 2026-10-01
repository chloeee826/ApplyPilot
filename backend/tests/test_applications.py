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
def clear_tracking_data():
    with TestSessionLocal() as session:
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(Application))
        session.execute(delete(Job))
        session.commit()


def create_tracked_job(client: TestClient) -> tuple[str, str]:
    job_response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "title": "Software Engineer",
            "description": "Build reliable services.",
        },
    )
    assert job_response.status_code == 201
    job_id = job_response.json()["id"]

    applications_response = client.get("/applications")
    assert applications_response.status_code == 200
    application = applications_response.json()[0]
    return job_id, application["id"]


def test_new_job_automatically_creates_saved_application(client: TestClient) -> None:
    job_id, _ = create_tracked_job(client)

    response = client.get("/applications")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["job_id"] == job_id
    assert response.json()[0]["status"] == "saved"


def test_update_application_status(client: TestClient) -> None:
    _, application_id = create_tracked_job(client)

    response = client.patch(
        f"/applications/{application_id}",
        json={"status": "interviewing"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "interviewing"

    with Session(test_engine) as session:
        saved_application = session.get(Application, UUID(application_id))

    assert saved_application is not None
    assert saved_application.status == "interviewing"


def test_update_application_rejects_invalid_status(client: TestClient) -> None:
    _, application_id = create_tracked_job(client)

    response = client.patch(
        f"/applications/{application_id}",
        json={"status": "waiting_forever"},
    )

    assert response.status_code == 422


def test_update_application_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.patch(
        "/applications/00000000-0000-0000-0000-000000000000",
        json={"status": "applied"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


def test_create_application_rejects_duplicate_job(client: TestClient) -> None:
    job_id, _ = create_tracked_job(client)

    response = client.post(
        "/applications",
        json={"job_id": job_id, "status": "saved"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Application already exists for this job"}


def test_list_applications_returns_updated_records(client: TestClient) -> None:
    job_id, application_id = create_tracked_job(client)
    client.patch(
        f"/applications/{application_id}",
        json={"status": "applied"},
    )

    response = client.get("/applications")

    assert response.status_code == 200
    assert response.json()[0]["job_id"] == job_id
    assert response.json()[0]["status"] == "applied"
