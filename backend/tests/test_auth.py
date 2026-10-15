"""Real guards, cookies and SQL ownership; no authentication dependency overrides."""

import time
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.migrations import upgrade_ownership
from app.models.agent_run import AgentRun
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.user import AuthSession, User
from app.security import COOKIE_NAME, PASSWORD_HASHER, token_hash

pytestmark = pytest.mark.auth
WRITE = {"X-ApplyPilot-Request": "1"}
PASSWORD = "synthetic-test-password-42"
JOB = {"company_name": "Private Co", "title": "Engineer", "description": "Build Python APIs. Docker preferred."}
PROFILE = {"full_name": "Private Candidate", "summary": "Builds APIs", "skills": ["Python"]}


@pytest.fixture
def auth_db(monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    monkeypatch.setattr("app.main.create_db_and_tables", lambda: Base.metadata.create_all(engine))

    def database():
        with Session(engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_db] = database
    yield engine
    app.dependency_overrides.clear()
    engine.dispose()


def account(email: str) -> TestClient:
    client = TestClient(app, headers=WRITE)
    response = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert response.status_code == 201, response.text
    return client


def test_password_hash_session_rotation_and_revocation(auth_db):
    with account("  Alice@Example.test ") as client:
        me = client.get("/auth/me")
        assert me.json()["email"] == "alice@example.test"
        assert "password" not in me.text
        assert me.headers["cache-control"] == "no-store"
        old_cookie = client.cookies.get(COOKIE_NAME)
        with Session(auth_db) as db:
            user = db.get(User, UUID(me.json()["id"]))
            assert user.password_hash.startswith("$argon2id$")
            assert PASSWORD_HASHER.verify(user.password_hash, PASSWORD)
            record = db.get(AuthSession, token_hash(old_cookie))
            assert record is not None
            assert record.token_hash != old_cookie
        login = client.post("/auth/login", json={"email": "alice@example.test", "password": PASSWORD})
        assert login.status_code == 200
        assert "httponly" in login.headers["set-cookie"].lower()
        assert "samesite=lax" in login.headers["set-cookie"].lower()
        assert client.cookies.get(COOKIE_NAME) != old_cookie
        with TestClient(app, cookies={COOKIE_NAME: old_cookie}) as revoked:
            assert revoked.get("/auth/me").status_code == 401
        new_cookie = client.cookies.get(COOKIE_NAME)
        assert client.post("/auth/logout").status_code == 204
        assert client.get("/jobs").status_code == 401
        with TestClient(app, cookies={COOKIE_NAME: new_cookie}) as revoked:
            assert revoked.get("/auth/me").status_code == 401


@pytest.mark.parametrize("path", ["/jobs", "/profiles", "/applications", "/job-analyses", "/agent-runs"])
def test_anonymous_reads_are_blocked(auth_db, path):
    with TestClient(app) as client:
        assert client.get(path).status_code == 401
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize("path,payload", [
    ("/jobs", JOB), ("/profiles", PROFILE), ("/candidate-imports", {"profile": PROFILE, "projects": []}),
    ("/fit-checks", {"request_id": str(uuid4()), "profile_id": str(uuid4()), "job": JOB}),
    ("/agent-runs", {"job_id": str(uuid4()), "profile_id": str(uuid4()), "mode": "demo"}),
])
def test_anonymous_writes_are_blocked(auth_db, path, payload):
    with TestClient(app, headers=WRITE) as client:
        assert client.post(path, json=payload).status_code == 401


def test_upload_requires_authentication(auth_db):
    with TestClient(app, headers=WRITE) as client:
        assert client.post("/resume-extractions", files={"resume": ("x.pdf", b"%PDF-test", "application/pdf")}).status_code == 401


def test_csrf_guards_cover_auth_json_and_multipart(auth_db):
    with TestClient(app) as client:
        assert client.post("/auth/register", json={"email": "x@example.test", "password": PASSWORD}).status_code == 403
    with account("csrf@example.test") as client:
        client.headers.pop("X-ApplyPilot-Request")
        assert client.post("/jobs", json=JOB).status_code == 403
        assert client.post("/auth/logout").status_code == 403
        assert client.post("/resume-extractions", files={"resume": ("x.pdf", b"%PDF-test", "application/pdf")}).status_code == 403
        client.headers.update(WRITE)
        assert client.post("/jobs", json=JOB, headers={"Origin": "https://evil.example"}).status_code == 403
        assert client.post("/jobs", json=JOB, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
        assert client.post("/jobs", json=JOB, headers={"Origin": "http://127.0.0.1:8008"}).status_code == 201


def test_expired_forged_and_secure_default_cookie(auth_db, monkeypatch):
    monkeypatch.delenv("AUTH_COOKIE_SECURE", raising=False)
    with TestClient(app, base_url="https://testserver", headers=WRITE) as client:
        response = client.post("/auth/register", json={"email": "secure@example.test", "password": PASSWORD})
        assert "secure" in response.headers["set-cookie"].lower()
        token = client.cookies.get(COOKIE_NAME)
        with Session(auth_db) as db:
            db.get(AuthSession, token_hash(token)).expires_at = int(time.time()) - 1
            db.commit()
        assert client.get("/auth/me").status_code == 401
    with TestClient(app, cookies={COOKIE_NAME: "f" * 43}) as client:
        assert client.get("/jobs").status_code == 401


def test_invalid_duplicate_login_and_rate_limit(auth_db):
    with account("limit@example.test") as client:
        assert client.post("/auth/register", json={"email": "LIMIT@example.test", "password": PASSWORD}).status_code == 409
        invalid = client.post("/auth/register", json={"email": "bad", "password": "tinyP@ss"})
        assert invalid.status_code == 422
        assert "tinyP@ss" not in invalid.text
        assert all("input" not in error for error in invalid.json()["detail"])
        for _ in range(10):
            bad = client.post("/auth/login", json={"email": "limit@example.test", "password": "wrong-password-long"})
            assert bad.status_code == 401
            assert bad.json() == {"detail": "Email or password is incorrect"}
        blocked = client.post("/auth/login", json={"email": "limit@example.test", "password": PASSWORD})
        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "900"


def test_two_users_cannot_read_write_link_or_run_each_others_evidence(auth_db):
    with account("owner@example.test") as alice, account("other@example.test") as bob:
        profile = alice.post("/profiles", json={**PROFILE, "owner_id": bob.get("/auth/me").json()["id"]}).json()
        fit_id = str(uuid4())
        payload = {"request_id": fit_id, "profile_id": profile["id"], "job": JOB}
        first = alice.post("/fit-checks", json=payload)
        assert first.status_code == 200, first.text
        result = first.json()
        assert alice.post("/fit-checks", json=payload).json()["report"]["id"] == result["report"]["id"]
        other_profile = bob.post("/profiles", json=PROFILE).json()
        other_job = bob.post("/jobs", json=JOB).json()
        for path in ("/job-analyses", "/agent-runs"):
            assert bob.get(path).json() == []
        assert {item["job_id"] for item in bob.get("/applications").json()} == {other_job["id"]}
        assert len(bob.get("/jobs").json()) == 1
        assert len(bob.get("/profiles").json()) == 1
        for path in (f"/jobs/{fit_id}", f"/profiles/{profile['id']}", f"/profiles/{profile['id']}/projects",
                     f"/job-analyses/{fit_id}", f"/agent-runs/{result['report']['id']}"):
            assert bob.get(path).status_code == 404
        for path, data in (
            (f"/jobs/{fit_id}", {"title": "Stolen"}),
            (f"/profiles/{profile['id']}", {"skills": ["Docker"]}),
            (f"/applications/{result['application']['id']}", {"status": "applied"}),
        ):
            assert bob.patch(path, json=data).status_code == 404
        assert bob.post(f"/job-analyses/{fit_id}").status_code == 404
        assert bob.post(f"/profiles/{profile['id']}/projects", json={"name": "Attack", "description": "x", "technologies": ["Python"], "highlights": ["Must not save"]}).status_code == 404
        assert bob.post("/candidate-imports", json={"profile_id": profile["id"], "profile": PROFILE, "projects": []}).status_code == 404
        assert bob.post("/applications", json={"job_id": fit_id}).status_code == 404
        for job_id, profile_id in ((fit_id, other_profile["id"]), (other_job["id"], profile["id"])):
            assert bob.post("/agent-runs", json={"job_id": job_id, "profile_id": profile_id, "mode": "demo"}).status_code == 404
            assert bob.post("/fit-checks", json={"request_id": job_id, "profile_id": profile_id, "job": JOB}).status_code == 404
        assert alice.get(f"/agent-runs/{result['report']['id']}").json()["context_status"] == "unchanged"
        with Session(auth_db) as db:
            assert db.get(CandidateProfile, UUID(profile["id"])).owner_id == UUID(alice.get("/auth/me").json()["id"])
            assert len(db.scalars(select(AgentRun)).all()) == 1


def test_legacy_data_stays_hidden_and_upgrade_is_idempotent(auth_db):
    with Session(auth_db) as db:
        legacy = Job(**JOB)
        db.add(legacy); db.commit()
        legacy_id = str(legacy.id)
    upgrade_ownership(auth_db)
    upgrade_ownership(auth_db)
    with account("first@example.test") as client:
        assert client.get("/jobs").json() == []
        assert client.get(f"/jobs/{legacy_id}").status_code == 404
    with Session(auth_db) as db:
        assert db.get(Job, UUID(legacy_id)) is not None


def test_upgrade_adds_nullable_ownership_to_old_tables_without_losing_rows():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE jobs (id CHAR(32) PRIMARY KEY, title TEXT)"))
        connection.execute(text("CREATE TABLE candidate_profiles (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("INSERT INTO jobs VALUES ('legacy', 'Keep this job')"))
    upgrade_ownership(engine)
    upgrade_ownership(engine)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT title, owner_id FROM jobs")).one() == ("Keep this job", None)
    engine.dispose()


def test_legacy_assignment_requires_explicit_confirmation_and_is_idempotent(auth_db):
    from scripts.assign_legacy import assign_legacy
    with account("operator@example.test") as client:
        user_id = UUID(client.get("/auth/me").json()["id"])
        with Session(auth_db) as db:
            db.add(Job(**JOB)); db.add(CandidateProfile(**PROFILE)); db.commit()
            counts = assign_legacy(db, user_id)
            assert counts == {"jobs": 1, "candidate_profiles": 1}
            assert client.get("/jobs").json() == []
            assert assign_legacy(db, user_id, confirm=True) == counts
            assert assign_legacy(db, user_id, confirm=True) == {"jobs": 0, "candidate_profiles": 0}
        assert len(client.get("/jobs").json()) == 1
        assert len(client.get("/profiles").json()) == 1


@pytest.mark.integration
@pytest.mark.skipif(__import__('os').getenv("RUN_POSTGRES_TESTS") != "1", reason="Opt-in dedicated PostgreSQL workspace only")
def test_postgres_real_sessions_persist_and_filter_other_users(monkeypatch):
    from app.database import SessionLocal, create_db_and_tables
    from sqlalchemy import delete
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    create_db_and_tables()
    user_ids = []
    suffix = uuid4().hex
    try:
        with account(f"pg-alice-{suffix}@example.test") as alice, account(f"pg-bob-{suffix}@example.test") as bob:
            user_ids = [UUID(client.get("/auth/me").json()["id"]) for client in (alice, bob)]
            profile = alice.post("/profiles", json=PROFILE).json()
            fit = alice.post("/fit-checks", json={"request_id": str(uuid4()), "profile_id": profile["id"], "job": JOB})
            assert fit.status_code == 200, fit.text
            report = fit.json()["report"]
            token = alice.cookies.get(COOKIE_NAME)
            with TestClient(app, cookies={COOKIE_NAME: token}) as another_request:
                assert another_request.get(f"/agent-runs/{report['id']}").json()["skill_coverage"]["percentage"] == 50.0
            assert bob.get("/jobs").json() == []
            assert bob.get("/profiles").json() == []
            assert bob.get("/agent-runs").json() == []
            assert bob.get(f"/agent-runs/{report['id']}").status_code == 404
            with SessionLocal() as db:
                assert db.get(Job, UUID(report["job_id"])).owner_id == user_ids[0]
    finally:
        if user_ids:
            with SessionLocal() as db:
                db.execute(delete(Job).where(Job.owner_id.in_(user_ids)))
                db.execute(delete(CandidateProfile).where(CandidateProfile.owner_id.in_(user_ids)))
                db.execute(delete(User).where(User.id.in_(user_ids)))
                db.commit()
