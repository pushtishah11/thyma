"""FastAPI dependencies shared by every router.

get_current_user is added in the next chunk, together with the users table.
"""

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db import SessionLocal


def get_db() -> Iterator[Session]:
    """One session per request, always closed when the request ends."""
    with SessionLocal() as session:
        yield session
