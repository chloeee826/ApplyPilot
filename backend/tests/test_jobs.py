from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_job() -> None:
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


def test_create_job_rejects_missing_required_field() -> None:
    response = client.post(
        "/jobs",
        json={
            "company_name": "Example Company",
            "description": "This request is missing a title.",
        },
    )

    assert response.status_code == 422


def test_create_job_rejects_invalid_source_url() -> None:
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
