import os
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.job import Job


@pytest.mark.integration
@pytest.mark.skipif(
    os.getenv("RUN_POSTGRES_TESTS") != "1",
    reason="Set RUN_POSTGRES_TESTS=1 to test the configured PostgreSQL database.",
)
def test_create_job_persists_in_postgres() -> None:
    with TestClient(app) as client:
        create_response = client.post(
            "/jobs",
            json={
                "company_name": "PostgreSQL Integration Test",
                "title": "Backend Engineer",
                "description": "Verify that the API persists this job.",
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

    with SessionLocal() as session:
        saved_job = session.get(Job, job_id)
        assert saved_job is not None
        assert saved_job.company_name == "PostgreSQL Integration Test"
        assert saved_job.title == "Senior Backend Engineer"

        session.delete(saved_job)
        session.commit()
