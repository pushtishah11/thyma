"""Database-level rules for cycles (a backstop behind the API's own checks)."""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Cycle, User


def test_end_before_start_is_rejected(db: Session, user: User) -> None:
    db.add(Cycle(user_id=user.id, start_date=date(2026, 3, 10), end_date=date(2026, 3, 9)))

    with pytest.raises(IntegrityError, match="cycles_end_after_start"):
        db.flush()


def test_same_start_twice_is_rejected_for_one_user(db: Session, user: User) -> None:
    db.add(Cycle(user_id=user.id, start_date=date(2026, 3, 10)))
    db.flush()
    db.add(Cycle(user_id=user.id, start_date=date(2026, 3, 10)))

    with pytest.raises(IntegrityError, match="cycles_user_start_key"):
        db.flush()


def test_two_users_can_share_a_start_date(db: Session, user: User, other_user: User) -> None:
    db.add_all(
        [
            Cycle(user_id=user.id, start_date=date(2026, 3, 10)),
            Cycle(user_id=other_user.id, start_date=date(2026, 3, 10)),
        ]
    )
    db.flush()  # no error
