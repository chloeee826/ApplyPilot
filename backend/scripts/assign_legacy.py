"""Local operator-only migration: preview, then explicitly assign unowned records."""

import argparse
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.database import SessionLocal, create_db_and_tables
from app.models.agent_run import AgentRun
from app.models.candidate import CandidateProfile
from app.models.job import Job
from app.models.user import User


def assign_legacy(db: Session, user_id: UUID, *, confirm: bool = False) -> dict[str, int]:
    if db.get(User, user_id) is None:
        raise ValueError("Create the intended account first")
    incompatible = db.scalar(select(AgentRun.id).join(Job)
        .join(CandidateProfile, CandidateProfile.id == AgentRun.profile_id).where(or_(
            (Job.owner_id.is_(None) & CandidateProfile.owner_id.is_not(None) & (CandidateProfile.owner_id != user_id)),
            (CandidateProfile.owner_id.is_(None) & Job.owner_id.is_not(None) & (Job.owner_id != user_id)),
        )).limit(1))
    if incompatible:
        raise ValueError("Cross-owner report found; inspect the legacy workspace manually")
    counts = {model.__tablename__: db.scalar(select(func.count()).select_from(model).where(model.owner_id.is_(None)))
              for model in (Job, CandidateProfile)}
    if confirm:
        for model in (Job, CandidateProfile):
            db.execute(update(model).where(model.owner_id.is_(None)).values(owner_id=user_id))
        db.commit()
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="Existing account that should own the pre-auth workspace")
    parser.add_argument("--confirm", action="store_true", help="Assign ALL currently unowned jobs/profiles; otherwise preview only")
    args = parser.parse_args()
    create_db_and_tables()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.strip().casefold()))
        if user is None:
            parser.error("Account not found. Register in the app first.")
        counts = assign_legacy(db, user.id, confirm=args.confirm)
    print("Assigned" if args.confirm else "Preview only; no ownership changed", counts)


if __name__ == "__main__":
    main()
