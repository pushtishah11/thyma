"""Fill the dev user with two weeks of SYNTHETIC logs, for trying the app.

    cd backend
    .venv/bin/python -m scripts.seed            # refuses if the dev user has any logs
    .venv/bin/python -m scripts.seed --reset    # deletes ALL of the dev user's logs first

Everything here is made up by a seeded random generator; none of it is real
health data. M6 replaces this with the full 5-month demo user.
"""

import argparse
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import DailyLog, User
from app.services.logs import upsert_log
from app.services.symptoms import list_tracked
from app.services.users import get_or_create_dev_user, update_user

DAYS = 14
# Two days left unlogged, so the Trends charts show what gaps look like.
SKIPPED_DAYS_AGO = {4, 9}


class AlreadyHasLogsError(Exception):
    """Seeding would mix synthetic logs with ones already there."""


def seed_two_weeks(db: Session, user: User, today: date, rng: random.Random) -> int:
    """Write up to 14 synthetic logs ending today. Returns how many were written."""
    existing = db.scalar(select(func.count()).where(DailyLog.user_id == user.id))
    if existing:
        raise AlreadyHasLogsError(f"user already has {existing} logs")

    if not user.conditions:
        # Both conditions, so every starter chip exists.
        update_user(db, user, conditions=["pcos", "thyroid"])
    chips = [t.symptom for t in list_tracked(db, user)]

    written = 0
    for days_ago in range(DAYS - 1, -1, -1):
        if days_ago in SKIPPED_DAYS_AGO:
            continue
        sleep = Decimal(rng.choice(range(10, 17))) / 2  # 5.0 to 8.0 hours, in half hours
        tired = sleep < 6.5
        energy = max(1, min(5, rng.randint(2, 4) - (1 if tired else 0)))
        mood = max(1, min(5, energy + rng.choice([-1, 0, 0, 1])))

        symptoms: dict[str, int] = {}
        # min(): a user may have hidden chips and have fewer than 3 left.
        for name in rng.sample(chips, k=min(rng.randint(0, 3), len(chips))):
            symptoms[name] = rng.randint(1, 3)
        # A loose pattern so the charts have something to show: short sleep, more fatigue.
        if tired and "fatigue" in chips:
            symptoms["fatigue"] = rng.randint(2, 3)

        upsert_log(
            db,
            user,
            today - timedelta(days=days_ago),
            energy=energy,
            mood=mood,
            sleep_hours=sleep,
            weight=None,
            notes=None,
            symptoms=sorted(symptoms.items()),
        )
        written += 1
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reset", action="store_true", help="delete ALL of the dev user's logs before seeding"
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        user = get_or_create_dev_user(db)
        if args.reset:
            deleted = db.execute(delete(DailyLog).where(DailyLog.user_id == user.id)).rowcount
            db.commit()
            print(f"Deleted {deleted} existing logs.")
        try:
            written = seed_two_weeks(db, user, date.today(), random.Random(42))
        except AlreadyHasLogsError as e:
            raise SystemExit(f"Not seeding: the dev {e}. Use --reset to replace them.") from None
        print(f"Wrote {written} synthetic logs for the last {DAYS} days.")


if __name__ == "__main__":
    main()
