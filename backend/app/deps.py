"""FastAPI dependencies shared by every router."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.services.users import get_or_create_dev_user


def get_db() -> Iterator[Session]:
    """One session per request, always closed when the request ends."""
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    """The user making the request.

    Phase 1: always the local dev user. M7 swaps this body for JWT validation
    plus a lookup by auth_sub; routers that depend on it don't change.
    """
    return get_or_create_dev_user(db)


CurrentUser = Annotated[User, Depends(get_current_user)]
