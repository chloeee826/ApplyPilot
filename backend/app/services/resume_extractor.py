import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.schemas.resume import ResumeProfileDraft, ResumeProjectDraft
from app.services.job_parser import SKILL_PATTERNS


PARSER_VERSION = "resume-rules-v2"
SECTION_HEADINGS = {
    "education",
    "experience",
    "work experience",
    "professional experience",
    "projects",
    "skills",
    "technical skills",
    "summary",
    "profile",
    "objective",
    "certifications",
    "awards",
}
CONTACT_PATTERN = re.compile(
    r"(?:@|https?://|linkedin\.com|github\.com|\+?\d[\d\s().-]{7,})",
    flags=re.IGNORECASE,
)


class ResumeExtractionError(ValueError):
    """Raised when a PDF cannot produce usable resume text."""


@dataclass(frozen=True)
class ExtractedPdf:
    text: str
    page_count: int


@dataclass(frozen=True)
class ParsedResume:
    profile: ResumeProfileDraft
    projects: list[ResumeProjectDraft]
    warnings: list[str]


def extract_pdf_text(pdf_bytes: bytes) -> ExtractedPdf:
    """Extract text from a non-encrypted, text-based PDF held in memory."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes), strict=False)
    except (PdfReadError, OSError, ValueError) as exc:
        raise ResumeExtractionError("The uploaded file is not a readable PDF.") from exc

    if reader.is_encrypted:
        raise ResumeExtractionError("Password-protected PDFs are not supported.")
    if not reader.pages:
        raise ResumeExtractionError("The PDF does not contain any pages.")

    try:
        page_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pypdf may surface format-specific decoding errors
        raise ResumeExtractionError("Text could not be extracted from this PDF.") from exc

    text = "\n".join(page_text).strip()
    if len(re.sub(r"\s+", "", text)) < 40:
        raise ResumeExtractionError(
            "No usable text was found. Upload a text-based PDF instead of a scanned image."
        )

    return ExtractedPdf(text=text, page_count=len(reader.pages))


def _clean_lines(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", line).strip(" •|\t")
        for line in text.splitlines()
        if re.sub(r"\s+", " ", line).strip(" •|\t")
    ]


def _is_heading(line: str) -> bool:
    normalized = line.casefold().rstrip(":")
    return normalized in SECTION_HEADINGS or (
        len(line) <= 32 and line.isupper() and len(line.split()) <= 4
    )


def _looks_like_name(line: str) -> bool:
    words = line.split()
    return (
        2 <= len(words) <= 6
        and len(line) <= 80
        and "," not in line
        and not _is_heading(line)
        and not CONTACT_PATTERN.search(line)
        and not any(char.isdigit() for char in line)
    )


def _name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = re.sub(r"[_-]+", " ", stem)
    cleaned = re.sub(r"(?i)\b(resume|cv|final|updated?)\b", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip().title() or "Candidate"


def _section_body(lines: list[str], names: set[str]) -> list[str]:
    start_index: int | None = None
    for index, line in enumerate(lines):
        if line.casefold().rstrip(":") in names:
            start_index = index + 1
            break
    if start_index is None:
        return []

    body: list[str] = []
    for line in lines[start_index:]:
        if _is_heading(line):
            break
        body.append(line)
    return body


def _project_section_lines(text: str) -> list[tuple[str, bool]]:
    """Return project-section lines while preserving bullet information."""
    raw_lines = text.splitlines()
    start_index: int | None = None
    for index, raw_line in enumerate(raw_lines):
        if raw_line.strip().casefold().rstrip(":") in {"projects", "selected projects"}:
            start_index = index + 1
            break
    if start_index is None:
        return []

    project_lines: list[tuple[str, bool]] = []
    for raw_line in raw_lines[start_index:]:
        stripped = re.sub(r"\s+", " ", raw_line).strip()
        if not stripped:
            continue
        cleaned = stripped.strip(" •*\t")
        if _is_heading(cleaned):
            break
        is_bullet = bool(re.match(r"^[\s]*[•*\-–—]", raw_line))
        project_lines.append((cleaned, is_bullet))
    return project_lines


def _skills_in_text(text: str) -> list[str]:
    normalized = text.casefold()
    return [
        skill
        for skill, pattern in SKILL_PATTERNS.items()
        if re.search(pattern, normalized, flags=re.IGNORECASE)
    ]


def _split_project_header(header: str) -> tuple[str, str]:
    for separator in (" | ", " — ", " – ", " - "):
        if separator in header:
            name, context = header.split(separator, maxsplit=1)
            return name.strip(), context.strip()
    return header.strip(), ""


def _parse_project_drafts(text: str) -> list[ResumeProjectDraft]:
    section_lines = _project_section_lines(text)
    projects: list[ResumeProjectDraft] = []
    current_header: str | None = None
    current_details: list[str] = []

    def save_current() -> None:
        nonlocal current_header, current_details
        if current_header is None or not current_details:
            return
        name, header_context = _split_project_header(current_header)
        project_text = " ".join([header_context, *current_details]).strip()
        projects.append(
            ResumeProjectDraft(
                name=name[:160],
                description=current_details[0][:2000],
                technologies=_skills_in_text(project_text)[:30],
                highlights=current_details[:20],
            )
        )

    for line, is_bullet in section_lines:
        if not is_bullet:
            save_current()
            current_header = line
            current_details = []
        elif current_header is not None:
            current_details.append(line.lstrip("-–— ").strip())

    save_current()
    return projects[:20]


def parse_resume_text(text: str, filename: str) -> ParsedResume:
    """Build a predictable draft; the caller must let the user review it."""
    lines = _clean_lines(text)
    if not lines:
        raise ResumeExtractionError("The resume did not contain readable text.")

    warnings = [
        "Review every field before saving; deterministic parsing can misread resume layouts.",
    ]
    header_lines: list[str] = []
    for line in lines[:8]:
        if _is_heading(line):
            break
        header_lines.append(line)
    name = next((line for line in header_lines if _looks_like_name(line)), None)
    if name is None:
        name = _name_from_filename(filename)
        warnings.append("The candidate name was inferred from the filename.")

    name_index = lines.index(name) if name in lines else -1
    headline = next(
        (
            line
            for line in lines[name_index + 1 : name_index + 5]
            if len(line) <= 160
            and not _is_heading(line)
            and not CONTACT_PATTERN.search(line)
        ),
        None,
    )

    summary_lines = _section_body(lines, {"summary", "profile", "objective"})
    if not summary_lines:
        summary_lines = [
            line
            for line in lines
            if line != name
            and line != headline
            and not _is_heading(line)
            and not CONTACT_PATTERN.search(line)
        ][:3]
        warnings.append("No summary section was found, so a short preview was inferred.")
    summary = " ".join(summary_lines)[:2000].strip()
    if not summary:
        raise ResumeExtractionError("A candidate summary could not be inferred.")

    skills = _skills_in_text(text)
    if not skills:
        warnings.append("No supported skills were detected; add them during review.")

    projects = _parse_project_drafts(text)
    if not projects:
        warnings.append(
            "No supported project layout was detected; add project evidence manually."
        )
    elif any(not project.technologies for project in projects):
        warnings.append("Some projects have no detected technologies; review them before saving.")

    return ParsedResume(
        profile=ResumeProfileDraft(
            full_name=name,
            headline=headline,
            summary=summary,
            skills=skills,
        ),
        projects=projects,
        warnings=warnings,
    )
