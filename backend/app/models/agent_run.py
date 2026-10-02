from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentRun(Base):
    """A persisted execution of the job-match recommendation agent."""

    __tablename__ = "agent_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        index=True,
    )
    profile_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)
    model: Mapped[str] = mapped_column(String(80))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    matched_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    skill_gaps: Mapped[list[str]] = mapped_column(JSON, default=list)
    project_evidence: Mapped[list[str]] = mapped_column(JSON, default=list)
    interview_focus: Mapped[list[str]] = mapped_column(JSON, default=list)
    tool_trace: Mapped[list[dict[str, object]]] = mapped_column(JSON, default=list)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
