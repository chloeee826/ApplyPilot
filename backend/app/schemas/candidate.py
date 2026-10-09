from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


ShortText = Annotated[str, Field(min_length=1, max_length=120)]
ListItem = Annotated[str, Field(min_length=1, max_length=200)]


class CandidateProfileCreate(BaseModel):
    """Candidate data supplied when creating a profile."""

    full_name: ShortText
    headline: str | None = Field(default=None, max_length=160)
    summary: str = Field(min_length=1, max_length=2000)
    skills: list[ShortText] = Field(min_length=1, max_length=50)


class CandidateProfileUpdate(BaseModel):
    """Candidate fields that may be changed after reviewing an import."""

    full_name: ShortText | None = None
    headline: str | None = Field(default=None, max_length=160)
    summary: str | None = Field(default=None, min_length=1, max_length=2000)
    skills: list[ShortText] | None = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> Self:
        for field_name in ("full_name", "summary", "skills"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


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
