from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import CandidateProfile, CandidateProject
from app.schemas.resume import CandidateImportCreate, CandidateImportRead


router = APIRouter(prefix="/candidate-imports", tags=["candidate imports"])


@router.post("", response_model=CandidateImportRead)
def save_candidate_import(
    candidate_import: CandidateImportCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CandidateImportRead:
    """Persist a reviewed profile and its projects in one transaction."""
    if candidate_import.profile_id is None:
        profile = CandidateProfile(**candidate_import.profile.model_dump())
        db.add(profile)
        db.flush()
    else:
        profile = db.get(CandidateProfile, candidate_import.profile_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate profile not found",
            )
        for field_name, value in candidate_import.profile.model_dump().items():
            setattr(profile, field_name, value)

    imported_projects: list[CandidateProject] = []
    created_count = 0
    updated_count = 0
    for project_data in candidate_import.projects:
        project = db.scalar(
            select(CandidateProject).where(
                CandidateProject.profile_id == profile.id,
                func.lower(CandidateProject.name) == project_data.name.strip().casefold(),
            )
        )
        if project is None:
            project = CandidateProject(
                profile_id=profile.id,
                **project_data.model_dump(),
            )
            db.add(project)
            created_count += 1
        else:
            for field_name, value in project_data.model_dump().items():
                setattr(project, field_name, value)
            updated_count += 1
        imported_projects.append(project)

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    db.refresh(profile)
    for project in imported_projects:
        db.refresh(project)

    return CandidateImportRead(
        profile=profile,
        projects=imported_projects,
        created_project_count=created_count,
        updated_project_count=updated_count,
    )
