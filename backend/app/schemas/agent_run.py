from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.services.match_evidence import MatchedSkillEvidence, explain_matches
from app.services.skill_ontology import SKILL_ONTOLOGY_VERSION
from app.services.skill_coverage import SkillCoverage, calculate_coverage


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
    context_status: Literal["unchanged", "changed", "unavailable"] = "unavailable"
    changed_sources: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def matched_skill_evidence(self) -> list[MatchedSkillEvidence]:
        return explain_matches(self.matched_skills, self.tool_trace, str(self.profile_id))

    @computed_field
    @property
    def evidence_ontology_version(self) -> str:
        """Version used for these read-time annotations, not historical execution."""
        return SKILL_ONTOLOGY_VERSION

    @computed_field
    @property
    def skill_coverage(self) -> SkillCoverage | None:
        if self.status != "completed":
            return None
        return calculate_coverage(self.tool_trace, str(self.job_id), str(self.profile_id))
