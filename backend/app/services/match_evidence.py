"""Explain reported matches using persisted tool snapshots, never current records."""

from typing import Literal

from pydantic import BaseModel, Field

from app.services.skill_ontology import canonicalize_skill


class EvidenceSource(BaseModel):
    source_type: Literal["profile", "project"]
    source_id: str
    source_name: str
    original_skill: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


class MatchedSkillEvidence(BaseModel):
    skill: str
    sources: list[EvidenceSource]


def explain_matches(
    matched_skills: list[str],
    tool_trace: list[dict[str, object]],
    profile_id: str,
) -> list[MatchedSkillEvidence]:
    """Resolve exact/known-alias support; missing or malformed traces stay unsupported.

    This is a read-time annotation using the current ontology, not a claim that
    the model's reasoning or the candidate's actual proficiency was verified.
    """
    sources: dict[str, list[EvidenceSource]] = {}

    def add(record: dict, kind: Literal["profile", "project"], field: str) -> None:
        values = record.get(field)
        source_id = record.get("id")
        if not isinstance(values, list) or not isinstance(source_id, str):
            return
        source_name = record.get("full_name" if kind == "profile" else "name")
        if not isinstance(source_name, str):
            return
        description = record.get("summary" if kind == "profile" else "description")
        highlights = record.get("highlights", [])
        for value in values:
            if not isinstance(value, str) or not value.strip():
                continue
            source = EvidenceSource(
                source_type=kind,
                source_id=source_id,
                source_name=source_name,
                original_skill=value,
                description=description if isinstance(description, str) else None,
                technologies=[item for item in values if isinstance(item, str)],
                highlights=[item for item in highlights if isinstance(item, str)]
                if isinstance(highlights, list) else [],
            )
            bucket = sources.setdefault(canonicalize_skill(value), [])
            if source not in bucket:
                bucket.append(source)

    for entry in tool_trace:
        output = entry.get("output")
        if not isinstance(output, dict):
            continue
        if entry.get("name") == "get_candidate_profile":
            if output.get("id") == profile_id:
                add(output, "profile", "skills")
        elif entry.get("name") == "list_candidate_projects":
            projects = output.get("projects")
            if isinstance(projects, list):
                for project in projects:
                    if isinstance(project, dict):
                        add(project, "project", "technologies")

    return [
        MatchedSkillEvidence(skill=skill, sources=sources.get(canonicalize_skill(skill), []))
        for skill in matched_skills
    ]
