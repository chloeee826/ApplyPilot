"""Existing business-unit tests isolate auth; test_auth exercises real cookies/guards."""

from typing import Annotated

import pytest
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.main import app
from app.security import get_workspace_db


@pytest.fixture(autouse=True)
def isolated_business_identity(request):
    if request.node.get_closest_marker("auth"):
        yield
        return

    def unit_workspace(db: Annotated[Session, Depends(get_db)]):
        # NULL-owned fixtures belong only to legacy business unit tests. There is
        # no such override or auth-disable configuration in the running product.
        db.info["owner_id"] = None
        return db

    app.dependency_overrides[get_workspace_db] = unit_workspace
    yield
    app.dependency_overrides.pop(get_workspace_db, None)
