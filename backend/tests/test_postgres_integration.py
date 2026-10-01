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
        response = client.post(
            "/jobs",
            json={
                "company_name": "PostgreSQL Integration Test",
                "title": "Backend Engineer",
                "description": "Verify that the API persists this job.",
            },
        )

    assert response.status_code == 201
    job_id = UUID(response.json()["id"])

    with SessionLocal() as session:
        saved_job = session.get(Job, job_id)
        assert saved_job is not None
        assert saved_job.company_name == "PostgreSQL Integration Test"

        session.delete(saved_job)
        session.commit()
