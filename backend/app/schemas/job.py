from datetime import datetime
from uuid import UUID

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class JobCreate(BaseModel):
    """Data supplied by a client when creating a job."""

    company_name: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None


class JobUpdate(BaseModel):
    """Fields that a client may change on an existing job."""

    company_name: str | None = Field(default=None, min_length=1, max_length=120)
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1)
    location: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> Self:
        for field_name in ("company_name", "title", "description"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class JobRead(JobCreate):
    """A created job returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
