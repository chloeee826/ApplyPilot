from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AgentRunCreate(BaseModel):
    """Stored records the agent should compare."""

    job_id: UUID
    profile_id: UUID
    mode: Literal["openai", "demo"] = "openai"


class AgentRunRead(BaseModel):
    """Persisted state and output of one agent execution."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    profile_id: UUID
    status: Literal["running", "completed", "failed"]
    model: str
    summary: str | None
    matched_skills: list[str]
    skill_gaps: list[str]
    project_evidence: list[str]
    interview_focus: list[str]
    tool_trace: list[dict[str, object]]
    error: str | None
    created_at: datetime
    completed_at: datetime | None
