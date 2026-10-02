import re
from dataclasses import dataclass


PARSER_VERSION = "rules-v1"

SKILL_PATTERNS = {
    "Python": r"\bpython\b",
    "Java": r"\bjava\b(?!script)",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b",
    "React": r"\breact(?:\.js|js)?\b",
    "FastAPI": r"\bfastapi\b",
    "SQL": r"\bsql\b",
    "PostgreSQL": r"\bpostgres(?:ql)?\b",
    "AWS": r"\baws\b|amazon web services",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "Git": r"\bgit\b",
    "REST APIs": r"\brest(?:ful)?\s+apis?\b",
    "Machine Learning": r"\bmachine learning\b|\bml\b",
    "LLMs": r"\blarge language models?\b|\bllms?\b",
    "CI/CD": r"\bci\s*/\s*cd\b|continuous integration",
    "Firebase": r"\bfirebase\b",
    "Android": r"\bandroid\b",
}

PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "bonus",
    "ideally",
    "a plus",
)
REQUIREMENT_MARKERS = (
    "required",
    "must have",
    "minimum",
    "experience with",
    "experience in",
    "proficiency",
    "proficient",
    "years of experience",
    "knowledge of",
    "familiarity with",
)
RESPONSIBILITY_MARKERS = (
    "build",
    "develop",
    "design",
    "implement",
    "maintain",
    "collaborate",
    "lead",
    "create",
    "deliver",
    "optimize",
    "test",
    "support",
    "own",
)


@dataclass(frozen=True)
class ParsedJobDescription:
    skills: list[str]
    requirements: list[str]
    preferred_qualifications: list[str]
    responsibilities: list[str]


def _segments(description: str) -> list[str]:
    raw_segments = re.split(r"(?:\r?\n)+|(?<=[.!?])\s+", description)
    cleaned: list[str] = []
    seen: set[str] = set()

    for segment in raw_segments:
        value = re.sub(r"^[\s•*\-–—\d.)]+", "", segment).strip()
        normalized = value.casefold()
        if len(value) < 4 or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(value)

    return cleaned


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    normalized = value.casefold()
    return any(marker in normalized for marker in markers)


def parse_job_description(description: str) -> ParsedJobDescription:
    """Extract predictable structured fields without calling an LLM."""
    segments = _segments(description)
    description_lower = description.casefold()

    skills = [
        skill
        for skill, pattern in SKILL_PATTERNS.items()
        if re.search(pattern, description_lower, flags=re.IGNORECASE)
    ]
    preferred = [
        segment
        for segment in segments
        if _contains_any(segment, PREFERRED_MARKERS)
    ]
    preferred_keys = {segment.casefold() for segment in preferred}
    requirements = [
        segment
        for segment in segments
        if segment.casefold() not in preferred_keys
        and _contains_any(segment, REQUIREMENT_MARKERS)
    ]
    responsibilities = [
        segment
        for segment in segments
        if _contains_any(segment, RESPONSIBILITY_MARKERS)
        and segment.casefold() not in preferred_keys
        and segment not in requirements
    ]

    return ParsedJobDescription(
        skills=skills,
        requirements=requirements[:12],
        preferred_qualifications=preferred[:12],
        responsibilities=responsibilities[:12],
    )
