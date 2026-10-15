"""Small local-account MVP; email is a login identifier, not verified identity."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import AuthSession, User
from app.security import (COOKIE_NAME, DUMMY_HASH, PASSWORD_HASHER, get_current_user,
                          issue_session, require_browser_write, throttle, token_hash, verify_password)

router = APIRouter(prefix="/auth", tags=["authentication"])


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=12, max_length=128, repr=False)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold() if isinstance(value, str) else value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str


def check_attempt(request: Request, db: Session, email: str, action: str) -> None:
    require_browser_write(request)
    # Do not trust client-supplied X-Forwarded-For without a configured proxy.
    host = request.client.host if request.client else "unknown"
    throttle(db, f"{action}:ip:{host}", limit=20)
    throttle(db, f"{action}:account:{email}")


@router.post("/register", response_model=UserRead, status_code=201)
def register(credentials: Credentials, request: Request, response: Response,
             db: Annotated[Session, Depends(get_db)]) -> User:
    check_attempt(request, db, credentials.email, "register")
    user = User(email=credentials.email, password_hash=PASSWORD_HASHER.hash(credentials.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Unable to create an account with these details") from exc
    issue_session(db, request, response, user)
    return user


@router.post("/login", response_model=UserRead)
def login(credentials: Credentials, request: Request, response: Response,
          db: Annotated[Session, Depends(get_db)]) -> User:
    check_attempt(request, db, credentials.email, "login")
    user = db.scalar(select(User).where(User.email == credentials.email))
    valid = verify_password(user.password_hash if user else DUMMY_HASH, credentials.password)
    if not valid or user is None:
        raise HTTPException(401, "Email or password is incorrect")
    if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
        user.password_hash = PASSWORD_HASHER.hash(credentials.password)
    issue_session(db, request, response, user)
    return user


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/logout", status_code=204, dependencies=[Depends(require_browser_write)])
def logout(request: Request, db: Annotated[Session, Depends(get_db)]) -> Response:
    # Idempotent even when the cookie has expired or was already revoked.
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(request.cookies.get(COOKIE_NAME, ""))))
    db.commit()
    response = Response(status_code=204)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
