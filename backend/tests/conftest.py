import os

# Point the app at the test database before any app module is imported,
# so tests can never read or write the real dev database.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://thyma:thyma@localhost:5432/thyma_test"
)

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine
from app.deps import get_current_user, get_db
from app.main import app
from app.models import User

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


@pytest.fixture(scope="session", autouse=True)
def migrated_database(alembic_config: Config) -> None:
    """Rebuild the test schema from the migrations once per test run.

    Going down to base first also proves every downgrade() works.
    """
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


@pytest.fixture
def db() -> Iterator[Session]:
    """A session whose changes are rolled back after the test.

    The outer transaction is never committed. Code under test that calls
    session.commit() only releases a savepoint inside it.
    """
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def user(db: Session) -> User:
    """A fresh user, separate from the dev user."""
    user = User(auth_sub="test|user-a")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def other_user(db: Session) -> User:
    """A second user, for proving one user's data never leaks to another."""
    user = User(auth_sub="test|user-b")
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def client(db: Session, user: User) -> Iterator[TestClient]:
    """The API, acting as `user`, inside the rolled-back test session.

    Not entered as a context manager, so the startup step (creating the dev
    user) doesn't run.
    """
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
