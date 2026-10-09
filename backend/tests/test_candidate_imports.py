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


def import_payload() -> dict:
    return {
        "profile": {
            "full_name": "Chloe Example",
            "headline": "Software Engineer",
            "summary": "Builds reliable AI-enabled products.",
            "skills": ["Python", "React", "FastAPI", "PostgreSQL"],
        },
        "projects": [
            {
                "name": "ApplyPilot",
                "description": "Built an agentic job-search workspace.",
                "technologies": ["React", "FastAPI", "PostgreSQL"],
                "highlights": ["Grounded recommendations in stored evidence."],
            }
        ],
    }


def test_candidate_import_creates_profile_and_projects_together(client: TestClient) -> None:
    response = client.post("/candidate-imports", json=import_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["full_name"] == "Chloe Example"
    assert body["projects"][0]["name"] == "ApplyPilot"
    assert body["created_project_count"] == 1
    assert body["updated_project_count"] == 0

    with Session(test_engine) as session:
        assert session.scalar(select(CandidateProfile)) is not None
        assert session.scalar(select(CandidateProject)) is not None


def test_reimport_updates_matching_project_instead_of_duplicating(
    client: TestClient,
) -> None:
    first = client.post("/candidate-imports", json=import_payload())
    profile_id = first.json()["profile"]["id"]
    updated_payload = import_payload()
    updated_payload["profile_id"] = profile_id
    updated_payload["projects"][0]["name"] = "applypilot"
    updated_payload["projects"][0]["highlights"] = ["Updated reviewed evidence."]

    response = client.post("/candidate-imports", json=updated_payload)

    assert response.status_code == 200
    assert response.json()["created_project_count"] == 0
    assert response.json()["updated_project_count"] == 1
    assert response.json()["projects"][0]["highlights"] == [
        "Updated reviewed evidence."
    ]

    with Session(test_engine) as session:
        projects = list(
            session.scalars(
                select(CandidateProject).where(
                    CandidateProject.profile_id == UUID(profile_id)
                )
            ).all()
        )
    assert len(projects) == 1


def test_candidate_import_rejects_duplicate_project_names(client: TestClient) -> None:
    payload = import_payload()
    payload["projects"].append(
        {
            **payload["projects"][0],
            "name": " applypilot ",
        }
    )

    response = client.post("/candidate-imports", json=payload)

    assert response.status_code == 422
    with Session(test_engine) as session:
        assert session.scalar(select(CandidateProfile)) is None
        assert session.scalar(select(CandidateProject)) is None


def test_candidate_import_returns_404_for_unknown_profile(client: TestClient) -> None:
    payload = import_payload()
    payload["profile_id"] = "00000000-0000-0000-0000-000000000000"

    response = client.post("/candidate-imports", json=payload)

    assert response.status_code == 404
    assert response.json() == {"detail": "Candidate profile not found"}
