from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ShortText = Annotated[str, Field(min_length=1, max_length=120)]
ListItem = Annotated[str, Field(min_length=1, max_length=200)]


class CandidateProfileCreate(BaseModel):
    """Candidate data supplied when creating a profile."""

    full_name: ShortText
    headline: str | None = Field(default=None, max_length=160)
    summary: str = Field(min_length=1, max_length=2000)
    skills: list[ShortText] = Field(min_length=1, max_length=50)


class CandidateProfileRead(CandidateProfileCreate):
    """A persisted candidate profile returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class CandidateProjectCreate(BaseModel):
    """Project evidence supplied for a candidate profile."""

    name: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=2000)
    technologies: list[ShortText] = Field(min_length=1, max_length=30)
    highlights: list[ListItem] = Field(min_length=1, max_length=20)


class CandidateProjectRead(CandidateProjectCreate):
    """Persisted project evidence returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    created_at: datetime
