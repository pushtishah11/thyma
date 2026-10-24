from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.deps import get_db
from app.main import app


def test_health_ok_when_database_is_reachable() -> None:
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}


def test_health_503_when_database_is_unreachable() -> None:
    # Nothing listens on port 1, so connecting fails fast with a real error.
    dead_engine = create_engine(
        "postgresql+psycopg://thyma:thyma@localhost:1/thyma",
        connect_args={"connect_timeout": 1},
    )

    def get_dead_db() -> Iterator[Session]:
        with Session(dead_engine) as session:
            yield session

    app.dependency_overrides[get_db] = get_dead_db
    try:
        response = TestClient(app).get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "db": "error"}


def test_health_is_only_under_api_prefix() -> None:
    assert TestClient(app).get("/health").status_code == 404
