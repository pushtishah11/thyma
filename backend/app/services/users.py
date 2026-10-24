"""The Phase 1 local dev user.

Until real auth lands in M7, every request acts as this one user. It has a fixed
id so it's the same row across restarts, and so tests can tell it apart.
"""

import uuid

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import User

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_or_create_dev_user(db: Session) -> User:
    # ON CONFLICT DO NOTHING makes this safe to call repeatedly, even from two
    # requests at the same moment.
    db.execute(insert(User).values(id=DEV_USER_ID).on_conflict_do_nothing(index_elements=["id"]))
    db.commit()
    user = db.get(User, DEV_USER_ID)
    assert user is not None
    return user
