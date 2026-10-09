from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileRead,
    CandidateProjectCreate,
    CandidateProjectRead,
)


class ResumeProfileDraft(BaseModel):
    """Editable candidate fields inferred from resume text."""

    full_name: str = Field(min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    summary: str = Field(min_length=1, max_length=2000)
    skills: list[str] = Field(max_length=50)


class ResumeProjectDraft(BaseModel):
    """Editable project evidence inferred from a resume section."""

    name: str = Field(min_length=1, max_length=160)
    description: str = Field(max_length=2000)
    technologies: list[str] = Field(max_length=30)
    highlights: list[str] = Field(max_length=20)


class ResumeExtractionRead(BaseModel):
    """A non-persisted preview created from an uploaded resume."""

    source_filename: str
    parser_version: str
    page_count: int = Field(ge=1)
    character_count: int = Field(ge=1)
    profile: ResumeProfileDraft
    projects: list[ResumeProjectDraft]
    warnings: list[str]


class CandidateImportCreate(BaseModel):
    """User-reviewed profile and project evidence saved as one transaction."""

    profile_id: UUID | None = None
    profile: CandidateProfileCreate
    projects: list[CandidateProjectCreate] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def project_names_must_be_unique(self) -> Self:
        names = [project.name.strip().casefold() for project in self.projects]
        if len(names) != len(set(names)):
            raise ValueError("project names must be unique within one import")
        return self


class CandidateImportRead(BaseModel):
    """Persisted result of one reviewed resume import."""

    profile: CandidateProfileRead
    projects: list[CandidateProjectRead]
    created_project_count: int = Field(ge=0)
    updated_project_count: int = Field(ge=0)
