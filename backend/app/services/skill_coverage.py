"""Transparent technical evidence coverage, independent of model-generated claims."""

import re

from pydantic import BaseModel

from app.services.job_parser import SKILL_PATTERNS
from app.services.match_evidence import MatchedSkillEvidence, explain_matches
from app.services.skill_ontology import canonicalize_skill


class SkillGapContext(BaseModel):
    skill: str
    excerpts: list[str]


class SkillCoverage(BaseModel):
    version: str = "coverage-v1"
    role_title: str
    company_name: str
    candidate_name: str
    supported_count: int
    total_count: int
    percentage: float | None
    supported: list[MatchedSkillEvidence]
    gaps: list[SkillGapContext]


def calculate_coverage(
    trace: list[dict[str, object]], job_id: str, profile_id: str,
) -> SkillCoverage | None:
    snapshots = {entry.get("name"): entry.get("output") for entry in trace}
    names = ("get_job", "get_job_analysis", "get_candidate_profile", "list_candidate_projects")
    if not all(isinstance(snapshots.get(name), dict) for name in names):
        return None
    job, analysis, profile, projects = (snapshots[name] for name in names)
    if job.get("id") != job_id or profile.get("id") != profile_id:
        return None
    if not isinstance(profile.get("skills"), list) or not isinstance(projects.get("projects"), list):
        return None
    skills = analysis.get("skills")
    if not isinstance(skills, list) or not all(isinstance(skill, str) for skill in skills):
        return None
    # Aliases and repeated extracted labels count once in the denominator.
    unique: dict[str, str] = {}
    for skill in skills:
        if skill.strip():
            unique.setdefault(canonicalize_skill(skill), skill)
    evidence = explain_matches(list(unique.values()), trace, profile_id)
    supported = [item for item in evidence if item.sources]
    description = job.get("description")
    sentences = re.split(r"(?:\r?\n)+|(?<=[.!?])\s+", description) if isinstance(description, str) else []
    gaps = []
    for item in evidence:
        if item.sources:
            continue
        pattern = next((value for name, value in SKILL_PATTERNS.items()
            if canonicalize_skill(name) == canonicalize_skill(item.skill)),
            r"(?<!\w)" + re.escape(item.skill) + r"(?!\w)")
        excerpts = list(dict.fromkeys(sentence.strip() for sentence in sentences
            if re.search(pattern, sentence, flags=re.IGNORECASE)))[:3]
        gaps.append(SkillGapContext(skill=item.skill, excerpts=excerpts))
    total = len(evidence)
    return SkillCoverage(
        role_title=str(job.get("title", "Saved role")),
        company_name=str(job.get("company_name", "Saved company")),
        candidate_name=str(profile.get("full_name", "Saved candidate")),
        supported_count=len(supported), total_count=total,
        percentage=round(100 * len(supported) / total, 1) if total else None,
        supported=supported, gaps=gaps,
    )
