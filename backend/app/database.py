import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://localhost:5432/applypilot",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class shared by all SQLAlchemy database models."""


def get_db() -> Generator[Session, None, None]:
    """Provide one database session for the duration of a request."""
    with SessionLocal() as session:
        yield session


def create_db_and_tables() -> None:
    """Create tables that do not yet exist in the configured database."""
    Base.metadata.create_all(bind=engine)
