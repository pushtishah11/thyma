"""User A can never read or modify user B's rows.

Keep this file passing forever. Every new user-owned endpoint gets a case here.
The client fixture acts as `user` (A); `other_user` is B.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DailyLog, LogSymptom, TrackedSymptom, User

DAY = date(2026, 1, 15)


@pytest.fixture
def b_log(db: Session, other_user: User) -> DailyLog:
    log = DailyLog(user_id=other_user.id, date=DAY, energy=1, mood=1, notes="B's private note")
    log.symptoms = [LogSymptom(user_id=other_user.id, symptom="acne", severity=3)]
    db.add(log)
    db.flush()
    return log


def test_a_cannot_list_bs_logs(client: TestClient, b_log: DailyLog) -> None:
    response = client.get("/api/logs", params={"start": "2026-01-01", "end": "2026-01-31"})

    assert response.json() == []


def test_a_writing_the_same_day_leaves_bs_log_alone(
    client: TestClient, db: Session, b_log: DailyLog
) -> None:
    client.put(f"/api/logs/{DAY}", json={"energy": 5, "symptoms": []})

    db.refresh(b_log)
    assert (b_log.energy, b_log.notes) == (1, "B's private note")
    assert [(s.symptom, s.severity) for s in b_log.symptoms] == [("acne", 3)]


def test_a_cannot_delete_bs_log(client: TestClient, db: Session, b_log: DailyLog) -> None:
    assert client.delete(f"/api/logs/{DAY}").status_code == 404

    assert db.get(DailyLog, b_log.id) is not None


def test_bs_logs_never_count_in_as_trends(client: TestClient, b_log: DailyLog) -> None:
    body = client.get("/api/trends", params={"start": "2026-01-15", "end": "2026-01-15"}).json()

    assert body["days_logged"] == 0
    assert body["symptoms"] == []
    assert body["daily"][0]["energy"] is None


def test_a_cannot_see_or_change_bs_chips(client: TestClient, db: Session, other_user: User) -> None:
    chip = TrackedSymptom(user_id=other_user.id, symptom="acne", position=0)
    db.add(chip)
    db.flush()
    url = f"/api/tracked-symptoms/{chip.id}"

    assert client.get("/api/tracked-symptoms", params={"include_inactive": True}).json() == []
    assert client.patch(url, json={"active": False}).status_code == 404
    assert client.delete(url).status_code == 404
    db.refresh(chip)
    assert chip.active is True

    # A adding a chip with the same name gets A's own chip; lists are per user.
    assert client.post("/api/tracked-symptoms", json={"symptom": "acne"}).status_code == 201


def test_a_changing_settings_does_not_touch_b(
    client: TestClient, db: Session, other_user: User
) -> None:
    client.patch("/api/me", json={"conditions": ["pcos"], "track_weight": True})

    db.refresh(other_user)
    assert (other_user.conditions, other_user.track_weight) == ([], False)
