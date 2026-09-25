from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class JobCreate(BaseModel):
    """Data supplied by a client when creating a job."""

    company_name: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=120)
    source_url: HttpUrl | None = None


class JobRead(JobCreate):
    """A created job returned by the API."""

    id: UUID
    created_at: datetime
