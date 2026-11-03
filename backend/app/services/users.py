"""Users: the Phase 1 local dev user, and updating a user's own settings.

Until real auth lands in M7, every request acts as the dev user. It has a fixed
id so it's the same row across restarts, and so tests can tell it apart.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import User
from app.services.symptoms import add_default_symptoms

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_or_create_dev_user(db: Session) -> User:
    # ON CONFLICT DO NOTHING makes this safe to call repeatedly, even from two
    # requests at the same moment.
    db.execute(insert(User).values(id=DEV_USER_ID).on_conflict_do_nothing(index_elements=["id"]))
    db.commit()
    user = db.get(User, DEV_USER_ID)
    assert user is not None
    return user


def update_user(
    db: Session,
    user: User,
    *,
    conditions: list[str] | None = None,
    track_cycles: bool | None = None,
    track_weight: bool | None = None,
    ai_consent: bool | None = None,
) -> User:
    """Apply the fields that were sent (None means "leave as is")."""
    if conditions is not None:
        user.conditions = sorted(set(conditions))
        # New conditions bring their starter symptom chips with them.
        add_default_symptoms(db, user)
    if track_cycles is not None:
        user.track_cycles = track_cycles
    if track_weight is not None:
        user.track_weight = track_weight
    if ai_consent is not None:
        user.ai_consent_at = datetime.now(UTC) if ai_consent else None
    db.commit()
    return user
