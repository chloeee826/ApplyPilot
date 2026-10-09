from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.candidate import CandidateProfile, CandidateProject


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
def clear_candidate_data():
    with TestSessionLocal() as session:
        session.execute(delete(CandidateProject))
        session.execute(delete(CandidateProfile))
        session.commit()

    yield

    with TestSessionLocal() as session:
        session.execute(delete(CandidateProject))
        session.execute(delete(CandidateProfile))
        session.commit()


def create_profile(client: TestClient) -> dict:
    response = client.post(
        "/profiles",
        json={
            "full_name": "Chloe Example",
            "headline": "Software Engineer",
            "summary": "Builds reliable full-stack products.",
            "skills": ["Python", "TypeScript", "PostgreSQL"],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_profile_persists_candidate_data(client: TestClient) -> None:
    body = create_profile(client)

    assert body["full_name"] == "Chloe Example"
    assert body["skills"] == ["Python", "TypeScript", "PostgreSQL"]

    with Session(test_engine) as session:
        saved_profile = session.get(CandidateProfile, UUID(body["id"]))

    assert saved_profile is not None
    assert saved_profile.headline == "Software Engineer"


def test_list_and_get_profiles(client: TestClient) -> None:
    profile = create_profile(client)

    list_response = client.get("/profiles")
    get_response = client.get(f"/profiles/{profile['id']}")

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == profile["id"]
    assert get_response.status_code == 200
    assert get_response.json()["summary"] == "Builds reliable full-stack products."


def test_create_profile_requires_at_least_one_skill(client: TestClient) -> None:
    response = client.post(
        "/profiles",
        json={
            "full_name": "Chloe Example",
            "summary": "Builds reliable products.",
            "skills": [],
        },
    )

    assert response.status_code == 422


def test_update_profile_saves_reviewed_resume_fields(client: TestClient) -> None:
    profile = create_profile(client)

    response = client.patch(
        f"/profiles/{profile['id']}",
        json={
            "headline": "AI Software Engineer",
            "summary": "Builds evidence-grounded agent workflows.",
            "skills": ["Python", "FastAPI", "React", "PostgreSQL"],
        },
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "Chloe Example"
    assert response.json()["headline"] == "AI Software Engineer"
    assert response.json()["skills"][-1] == "PostgreSQL"

    with Session(test_engine) as session:
        saved_profile = session.get(CandidateProfile, UUID(profile["id"]))

    assert saved_profile is not None
    assert saved_profile.summary == "Builds evidence-grounded agent workflows."


def test_update_profile_rejects_null_required_field(client: TestClient) -> None:
    profile = create_profile(client)

    response = client.patch(
        f"/profiles/{profile['id']}",
        json={"full_name": None},
    )

    assert response.status_code == 422


def test_update_profile_returns_404_for_unknown_profile(client: TestClient) -> None:
    response = client.patch(
        "/profiles/00000000-0000-0000-0000-000000000000",
        json={"headline": "Software Engineer"},
    )

    assert response.status_code == 404


def test_create_project_persists_evidence(client: TestClient) -> None:
    profile = create_profile(client)
    response = client.post(
        f"/profiles/{profile['id']}/projects",
        json={
            "name": "ApplyPilot",
            "description": "An agentic job search workspace.",
            "technologies": ["React", "FastAPI", "PostgreSQL"],
            "highlights": [
                "Built persistent job and application tracking.",
                "Added real PostgreSQL integration tests.",
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["profile_id"] == profile["id"]
    assert response.json()["highlights"][0].startswith("Built persistent")

    with Session(test_engine) as session:
        saved_project = session.scalar(
            select(CandidateProject).where(
                CandidateProject.id == UUID(response.json()["id"])
            )
        )

    assert saved_project is not None
    assert saved_project.technologies == ["React", "FastAPI", "PostgreSQL"]


def test_create_project_returns_404_for_unknown_profile(client: TestClient) -> None:
    response = client.post(
        "/profiles/00000000-0000-0000-0000-000000000000/projects",
        json={
            "name": "Unknown project",
            "description": "This profile does not exist.",
            "technologies": ["Python"],
            "highlights": ["Should not be saved."],
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Candidate profile not found"}


def test_list_projects_returns_profile_evidence(client: TestClient) -> None:
    profile = create_profile(client)
    create_response = client.post(
        f"/profiles/{profile['id']}/projects",
        json={
            "name": "ApplyPilot",
            "description": "An agentic job search workspace.",
            "technologies": ["Python"],
            "highlights": ["Created an evidence store."],
        },
    )
    assert create_response.status_code == 201

    response = client.get(f"/profiles/{profile['id']}/projects")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "ApplyPilot"
