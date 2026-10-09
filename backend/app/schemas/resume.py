from pydantic import BaseModel, Field


class ResumeProfileDraft(BaseModel):
    """Editable candidate fields inferred from resume text."""

    full_name: str = Field(min_length=1, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    summary: str = Field(min_length=1, max_length=2000)
    skills: list[str] = Field(max_length=50)


class ResumeExtractionRead(BaseModel):
    """A non-persisted preview created from an uploaded resume."""

    source_filename: str
    parser_version: str
    page_count: int = Field(ge=1)
    character_count: int = Field(ge=1)
    profile: ResumeProfileDraft
    warnings: list[str]
