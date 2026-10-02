from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CandidateProfile(Base):
    """Candidate information the agent may use as factual context."""

    __tablename__ = "candidate_profiles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(120))
    headline: Mapped[str | None] = mapped_column(String(160), nullable=True)
    summary: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class CandidateProject(Base):
    """Project evidence linked to a candidate profile."""

    __tablename__ = "candidate_projects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list)
    highlights: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
