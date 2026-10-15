"""Authentication dependencies and explicit resource ownership checks."""

import hashlib
import os
import secrets
import time
from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import AuthSession, AuthThrottle, User

COOKIE_NAME = "applypilot_session"
SESSION_SECONDS = 8 * 60 * 60
PASSWORD_HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
DUMMY_HASH = PASSWORD_HASHER.hash(secrets.token_urlsafe(24))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(encoded: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(encoded, password)
    except VerificationError:
        return False


def require_browser_write(request: Request) -> None:
    # Custom headers cannot be sent by cross-origin HTML forms. No CORS middleware
    # grants other origins permission to send this header, including PDF uploads.
    if request.headers.get("X-ApplyPilot-Request") != "1":
        raise HTTPException(403, "Missing request protection header")
    defaults = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8008,http://localhost:8008"
    allowed = {item.strip() for item in os.getenv("APP_ORIGINS", defaults).split(",")}
    origin = request.headers.get("origin")
    if (origin and origin not in allowed) or request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Origin not allowed")


def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(COOKIE_NAME, "")
    record = db.get(AuthSession, token_hash(token)) if 20 <= len(token) <= 128 else None
    if record is None or record.expires_at <= int(time.time()):
        raise HTTPException(401, "Sign in to continue")
    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(401, "Sign in to continue")
    return user


def get_workspace_db(request: Request, user: Annotated[User, Depends(get_current_user)],
                     db: Annotated[Session, Depends(get_db)]) -> Session:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_browser_write(request)
    db.info["owner_id"] = user.id
    return db


def current_owner(db: Session) -> UUID:
    # Fail closed if a route forgets the authenticated database dependency.
    if "owner_id" not in db.info:
        raise RuntimeError("Workspace query requires an authenticated owner")
    return db.info["owner_id"]


def owned(db: Session, model, resource_id: UUID):
    record = db.scalar(select(model).where(model.id == resource_id, model.owner_id == current_owner(db)))
    if record is None:
        # Foreign IDs deliberately look identical to absent IDs.
        label = {"jobs": "Job", "candidate_profiles": "Candidate profile"}.get(model.__tablename__, "Resource")
        raise HTTPException(404, f"{label} not found")
    return record


def issue_session(db: Session, request: Request, response: Response, user: User) -> None:
    old = request.cookies.get(COOKIE_NAME)
    if old:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(old)))
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= int(time.time())))
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id,
                       expires_at=int(time.time()) + SESSION_SECONDS))
    db.commit()
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=os.getenv("AUTH_COOKIE_SECURE", "true").lower() != "false",
                        samesite="lax", path="/")


def throttle(db: Session, key: str, limit: int = 10) -> None:
    """Database-backed fixed window; atomic increments also work across workers."""
    key = token_hash(key)
    now = int(time.time())
    db.execute(delete(AuthThrottle).where(AuthThrottle.expires_at <= now))
    count = db.scalar(update(AuthThrottle).where(AuthThrottle.key == key)
                      .values(attempts=AuthThrottle.attempts + 1).returning(AuthThrottle.attempts))
    if count is None:
        db.add(AuthThrottle(key=key, attempts=1, expires_at=now + 900))
        try:
            db.commit()
            count = 1
        except IntegrityError:
            db.rollback()
            count = db.scalar(update(AuthThrottle).where(AuthThrottle.key == key)
                              .values(attempts=AuthThrottle.attempts + 1).returning(AuthThrottle.attempts))
            db.commit()
    else:
        db.commit()
    if count is None or count > limit:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.", headers={"Retry-After": "900"})
