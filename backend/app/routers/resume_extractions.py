from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.resume import ResumeExtractionRead
from app.services.resume_extractor import (
    PARSER_VERSION,
    ResumeExtractionError,
    extract_pdf_text,
    parse_resume_text,
)


router = APIRouter(prefix="/resume-extractions", tags=["resume extractions"])

MAX_RESUME_BYTES = 5 * 1024 * 1024
PDF_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}


@router.post("", response_model=ResumeExtractionRead)
async def preview_resume(
    resume: UploadFile = File(description="A text-based PDF resume, up to 5 MB."),
) -> ResumeExtractionRead:
    """Return an editable draft without persisting the original file or its text."""
    filename = Path(resume.filename or "resume.pdf").name
    if Path(filename).suffix.casefold() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF resumes are supported.",
        )
    if resume.content_type not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF resumes are supported.",
        )

    contents = await resume.read(MAX_RESUME_BYTES + 1)
    await resume.close()
    if len(contents) > MAX_RESUME_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Resume must be 5 MB or smaller.",
        )
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded file does not have a valid PDF header.",
        )

    try:
        extracted = extract_pdf_text(contents)
        parsed = parse_resume_text(extracted.text, filename)
    except ResumeExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    return ResumeExtractionRead(
        source_filename=filename,
        parser_version=PARSER_VERSION,
        page_count=extracted.page_count,
        character_count=len(extracted.text),
        profile=parsed.profile,
        warnings=parsed.warnings,
    )
