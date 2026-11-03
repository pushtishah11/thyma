"""Database-level rules for daily logs and symptoms.

The API validates first; these prove the check constraints still catch bad
rows if something slips past it.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import DailyLog, LogSymptom, TrackedSymptom, User

DAY = date(2026, 1, 15)


def make_log(user: User, **fields: object) -> DailyLog:
    return DailyLog(user_id=user.id, date=DAY, **fields)


def test_log_with_symptoms_round_trips(db: Session, user: User) -> None:
    log = make_log(user, energy=3, mood=4, sleep_hours=Decimal("7.5"), notes="ok day")
    log.symptoms = [
        LogSymptom(user_id=user.id, symptom="fatigue", severity=2),
        LogSymptom(user_id=user.id, symptom="acne", severity=1),
    ]
    db.add(log)
    db.flush()
    db.expire_all()

    saved = db.scalars(select(DailyLog).where(DailyLog.user_id == user.id)).one()
    assert saved.sleep_hours == Decimal("7.5")
    # Symptoms come back in alphabetical order (relationship order_by).
    assert [(s.symptom, s.severity) for s in saved.symptoms] == [("acne", 1), ("fatigue", 2)]


@pytest.mark.parametrize(
    ("fields", "constraint"),
    [
        ({"energy": 0}, "daily_logs_energy_range"),
        ({"energy": 6}, "daily_logs_energy_range"),
        ({"mood": 0}, "daily_logs_mood_range"),
        ({"mood": 6}, "daily_logs_mood_range"),
        ({"sleep_hours": Decimal("-1")}, "daily_logs_sleep_range"),
        ({"sleep_hours": Decimal("24.5")}, "daily_logs_sleep_range"),
    ],
)
def test_out_of_range_log_values_are_rejected(
    db: Session, user: User, fields: dict[str, object], constraint: str
) -> None:
    db.add(make_log(user, **fields))

    with pytest.raises(IntegrityError, match=constraint):
        db.flush()


def test_one_log_per_user_per_day(db: Session, user: User) -> None:
    db.add_all([make_log(user), make_log(user)])

    with pytest.raises(IntegrityError, match="daily_logs_user_date_key"):
        db.flush()


def test_two_users_can_log_the_same_day(db: Session, user: User, other_user: User) -> None:
    db.add_all([make_log(user), make_log(other_user)])
    db.flush()


@pytest.mark.parametrize(
    ("symptom", "severity", "constraint"),
    [
        ("acne", 0, "log_symptoms_severity_range"),
        ("acne", 4, "log_symptoms_severity_range"),
        ("Acne", 2, "log_symptoms_symptom_lowercase"),
    ],
)
def test_bad_symptom_rows_are_rejected(
    db: Session, user: User, symptom: str, severity: int, constraint: str
) -> None:
    log = make_log(user)
    log.symptoms = [LogSymptom(user_id=user.id, symptom=symptom, severity=severity)]
    db.add(log)

    with pytest.raises(IntegrityError, match=constraint):
        db.flush()


def test_same_symptom_twice_in_one_log_is_rejected(db: Session, user: User) -> None:
    log = make_log(user)
    log.symptoms = [
        LogSymptom(user_id=user.id, symptom="acne", severity=1),
        LogSymptom(user_id=user.id, symptom="acne", severity=3),
    ]
    db.add(log)

    with pytest.raises(IntegrityError, match="log_symptoms_log_symptom_key"):
        db.flush()


def test_deleting_a_log_deletes_its_symptoms(db: Session, user: User) -> None:
    log = make_log(user)
    log.symptoms = [LogSymptom(user_id=user.id, symptom="acne", severity=1)]
    db.add(log)
    db.flush()

    db.delete(log)
    db.flush()

    assert db.scalar(select(func.count()).select_from(LogSymptom)) == 0


def test_deleting_a_user_deletes_their_logs_and_chips(db: Session, user: User) -> None:
    log = make_log(user)
    log.symptoms = [LogSymptom(user_id=user.id, symptom="acne", severity=1)]
    db.add_all([log, TrackedSymptom(user_id=user.id, symptom="acne", position=0)])
    db.flush()

    db.delete(user)
    db.flush()

    for table in (DailyLog, LogSymptom, TrackedSymptom):
        assert db.scalar(select(func.count()).select_from(table)) == 0


def test_tracked_symptom_is_unique_per_user(db: Session, user: User, other_user: User) -> None:
    db.add_all(
        [
            TrackedSymptom(user_id=user.id, symptom="acne", position=0),
            TrackedSymptom(user_id=other_user.id, symptom="acne", position=0),
        ]
    )
    db.flush()

    db.add(TrackedSymptom(user_id=user.id, symptom="acne", position=1))
    with pytest.raises(IntegrityError, match="tracked_symptoms_user_symptom_key"):
        db.flush()


def test_tracked_symptom_must_be_lowercase(db: Session, user: User) -> None:
    db.add(TrackedSymptom(user_id=user.id, symptom="Brain Fog", position=0))

    with pytest.raises(IntegrityError, match="tracked_symptoms_symptom_lowercase"):
        db.flush()
