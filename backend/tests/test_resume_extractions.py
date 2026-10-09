from fastapi.testclient import TestClient

from app.main import app
from app.routers import resume_extractions
from app.services.resume_extractor import ExtractedPdf, parse_resume_text


def test_parse_resume_text_returns_reviewable_profile_draft() -> None:
    parsed = parse_resume_text(
        """Chloe Example
Software Engineer
chloe@example.com | github.com/chloe

SUMMARY
Full-stack engineer building reliable AI-enabled products.

SKILLS
Python, TypeScript, React, FastAPI, PostgreSQL, Docker
""",
        "chloe-example-resume.pdf",
    )

    assert parsed.profile.full_name == "Chloe Example"
    assert parsed.profile.headline == "Software Engineer"
    assert parsed.profile.summary == (
        "Full-stack engineer building reliable AI-enabled products."
    )
    assert parsed.profile.skills == [
        "Python",
        "TypeScript",
        "React",
        "FastAPI",
        "PostgreSQL",
        "Docker",
    ]
    assert any("Review every field" in warning for warning in parsed.warnings)


def test_parse_resume_text_uses_filename_when_name_is_missing() -> None:
    parsed = parse_resume_text(
        """SUMMARY
Backend engineer with Python and PostgreSQL experience.
SKILLS
Python, PostgreSQL
EXPERIENCE
Built REST APIs for production services.
""",
        "chloe_lee_resume_final.pdf",
    )

    assert parsed.profile.full_name == "Chloe Lee"
    assert any("inferred from the filename" in warning for warning in parsed.warnings)


def test_parse_resume_text_returns_reviewable_project_drafts() -> None:
    parsed = parse_resume_text(
        """Chloe Example
Software Engineer
SUMMARY
Builds full-stack products with Python and React.
PROJECTS
ApplyPilot | React, FastAPI, PostgreSQL
- Built a persistent job and application tracking workflow.
- Developed evidence-grounded agent recommendations with Python.
TaskForge | Java, Firebase, Android
- Implemented scheduled task reminders for mobile users.
EDUCATION
Northeastern University
""",
        "chloe-example.pdf",
    )

    assert [project.name for project in parsed.projects] == [
        "ApplyPilot",
        "TaskForge",
    ]
    assert parsed.projects[0].technologies == [
        "Python",
        "React",
        "FastAPI",
        "PostgreSQL",
    ]
    assert parsed.projects[0].highlights[0].startswith("Built a persistent")
    assert parsed.projects[1].technologies == ["Java", "Firebase", "Android"]


def test_preview_resume_returns_draft_without_persisting_file(monkeypatch) -> None:
    monkeypatch.setattr(
        resume_extractions,
        "extract_pdf_text",
        lambda _: ExtractedPdf(
            text=(
                "Chloe Example\nSoftware Engineer\nSUMMARY\n"
                "Builds products with Python, React, FastAPI, and PostgreSQL."
            ),
            page_count=1,
        ),
    )

    client = TestClient(app)
    try:
        response = client.post(
            "/resume-extractions",
            files={"resume": ("chloe.pdf", b"%PDF-fake-test", "application/pdf")},
        )
    finally:
        client.close()

    assert response.status_code == 200
    body = response.json()
    assert body["source_filename"] == "chloe.pdf"
    assert body["parser_version"] == "resume-rules-v2"
    assert body["page_count"] == 1
    assert body["profile"]["full_name"] == "Chloe Example"
    assert "Python" in body["profile"]["skills"]
    assert body["projects"] == []


def test_preview_resume_rejects_non_pdf_upload() -> None:
    client = TestClient(app)
    try:
        response = client.post(
            "/resume-extractions",
            files={"resume": ("resume.txt", b"not a pdf", "text/plain")},
        )
    finally:
        client.close()

    assert response.status_code == 415
    assert response.json() == {"detail": "Only PDF resumes are supported."}


def test_preview_resume_rejects_fake_pdf_content() -> None:
    client = TestClient(app)
    try:
        response = client.post(
            "/resume-extractions",
            files={"resume": ("resume.pdf", b"not a pdf", "application/pdf")},
        )
    finally:
        client.close()

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The uploaded file does not have a valid PDF header."
    }


def test_preview_resume_rejects_files_larger_than_five_mb() -> None:
    oversized_pdf = b"%PDF-" + b"0" * (5 * 1024 * 1024)

    client = TestClient(app)
    try:
        response = client.post(
            "/resume-extractions",
            files={"resume": ("large.pdf", oversized_pdf, "application/pdf")},
        )
    finally:
        client.close()

    assert response.status_code == 413
    assert response.json() == {"detail": "Resume must be 5 MB or smaller."}
