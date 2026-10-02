from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.candidate import CandidateProfile, CandidateProject
from app.schemas.candidate import (
    CandidateProfileCreate,
    CandidateProfileRead,
    CandidateProjectCreate,
    CandidateProjectRead,
)


router = APIRouter(prefix="/profiles", tags=["profiles"])


def get_profile_or_404(db: Session, profile_id: UUID) -> CandidateProfile:
    profile = db.get(CandidateProfile, profile_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )
    return profile


@router.post("", response_model=CandidateProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile: CandidateProfileCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CandidateProfile:
    record = CandidateProfile(**profile.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[CandidateProfileRead])
def list_profiles(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[CandidateProfile]:
    statement = (
        select(CandidateProfile)
        .order_by(CandidateProfile.created_at.desc(), CandidateProfile.id)
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{profile_id}", response_model=CandidateProfileRead)
def get_profile(
    profile_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> CandidateProfile:
    return get_profile_or_404(db, profile_id)


@router.post(
    "/{profile_id}/projects",
    response_model=CandidateProjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    profile_id: UUID,
    project: CandidateProjectCreate,
    db: Annotated[Session, Depends(get_db)],
) -> CandidateProject:
    get_profile_or_404(db, profile_id)
    record = CandidateProject(profile_id=profile_id, **project.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{profile_id}/projects", response_model=list[CandidateProjectRead])
def list_projects(
    profile_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> list[CandidateProject]:
    get_profile_or_404(db, profile_id)
    statement = (
        select(CandidateProject)
        .where(CandidateProject.profile_id == profile_id)
        .order_by(CandidateProject.created_at.desc(), CandidateProject.id)
    )
    return list(db.scalars(statement).all())
