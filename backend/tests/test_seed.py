import random
from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.models import User
from app.services.logs import list_logs
from app.services.symptoms import list_tracked
from scripts.seed import AlreadyHasLogsError, seed_two_weeks

TODAY = date(2026, 3, 14)
START = date(2026, 3, 1)


def test_seed_writes_two_weeks_with_two_gaps(db: Session, user: User) -> None:
    written = seed_two_weeks(db, user, TODAY, random.Random(1))

    logs = list_logs(db, user, date(2026, 1, 1), date(2026, 12, 31))
    assert written == len(logs) == 12
    assert logs[0].date == START and logs[-1].date == TODAY
    assert {date(2026, 3, 10), date(2026, 3, 5)}.isdisjoint(log.date for log in logs)


def test_seeded_values_are_in_range_and_use_the_users_chips(db: Session, user: User) -> None:
    seed_two_weeks(db, user, TODAY, random.Random(1))

    chips = {t.symptom for t in list_tracked(db, user)}
    assert user.conditions == ["pcos", "thyroid"]
    for log in list_logs(db, user, START, TODAY):
        assert 1 <= log.energy <= 5 and 1 <= log.mood <= 5
        assert 5 <= log.sleep_hours <= 8
        assert log.weight is None
        assert {s.symptom for s in log.symptoms} <= chips
        assert all(1 <= s.severity <= 3 for s in log.symptoms)


def test_same_seed_gives_the_same_data(db: Session, user: User, other_user: User) -> None:
    seed_two_weeks(db, user, TODAY, random.Random(7))
    seed_two_weeks(db, other_user, TODAY, random.Random(7))

    def snapshot(u: User) -> list[tuple]:
        return [
            (
                log.date,
                log.energy,
                log.mood,
                log.sleep_hours,
                [(s.symptom, s.severity) for s in log.symptoms],
            )
            for log in list_logs(db, u, START, TODAY)
        ]

    assert snapshot(user) == snapshot(other_user)


def test_seed_refuses_when_logs_already_exist(db: Session, user: User) -> None:
    seed_two_weeks(db, user, TODAY, random.Random(1))

    with pytest.raises(AlreadyHasLogsError):
        seed_two_weeks(db, user, TODAY, random.Random(1))


def test_seed_keeps_conditions_the_user_already_picked(db: Session, user: User) -> None:
    user.conditions = ["thyroid"]
    db.flush()

    seed_two_weeks(db, user, TODAY, random.Random(1))

    assert user.conditions == ["thyroid"]
