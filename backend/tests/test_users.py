import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.deps import get_current_user
from app.main import app
from app.models import User
from app.services.users import DEV_USER_ID, get_or_create_dev_user


def test_dev_user_has_spec_defaults(db: Session) -> None:
    user = get_or_create_dev_user(db)

    assert user.id == DEV_USER_ID
    assert user.auth_sub is None
    assert user.conditions == []
    assert user.track_cycles is True
    assert user.track_weight is False
    assert user.ai_consent_at is None
    assert user.created_at is not None


def test_get_or_create_dev_user_is_idempotent(db: Session) -> None:
    first = get_or_create_dev_user(db)
    second = get_or_create_dev_user(db)

    assert first.id == second.id
    assert db.scalar(select(func.count()).select_from(User)) == 1


def test_get_current_user_returns_the_dev_user(db: Session) -> None:
    assert get_current_user(db).id == DEV_USER_ID


def test_known_conditions_are_accepted(db: Session) -> None:
    db.add(User(conditions=["pcos", "thyroid"]))
    db.flush()


def test_unknown_condition_is_rejected_by_the_database(db: Session) -> None:
    db.add(User(conditions=["pcos", "diabetes"]))

    with pytest.raises(IntegrityError, match="users_conditions_known"):
        db.flush()


def test_auth_sub_is_unique(db: Session) -> None:
    db.add_all([User(auth_sub="auth0|abc"), User(auth_sub="auth0|abc")])

    with pytest.raises(IntegrityError):
        db.flush()


def test_app_startup_creates_the_dev_user() -> None:
    # Entering the TestClient context runs the lifespan startup.
    with TestClient(app):
        pass

    with SessionLocal() as db:
        assert db.get(User, DEV_USER_ID) is not None
