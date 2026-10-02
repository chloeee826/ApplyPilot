from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobAnalysisRead(BaseModel):
    """Structured analysis returned for a stored job description."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    job_id: UUID
    skills: list[str]
    requirements: list[str]
    preferred_qualifications: list[str]
    responsibilities: list[str]
    parser_version: str
    created_at: datetime
    updated_at: datetime
