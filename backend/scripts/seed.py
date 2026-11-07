"""Fill the dev user with SYNTHETIC data, for trying the app.

    cd backend
    .venv/bin/python -m scripts.seed            # fills only the parts that are empty
    .venv/bin/python -m scripts.seed --reset    # deletes ALL of the dev user's data first

Two parts, each skipped if the dev user already has that kind of data:
  1. two weeks of daily logs
  2. three periods, three meds/supplements with two weeks of doses, and two weeks of meals

Everything here is made up by a seeded random generator; none of it is real
health data. M6 replaces this with the full 5-month demo user.
"""

import argparse
import random
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Cycle, DailyLog, Meal, Medication, User, UserFoodTag
from app.services import cycle_records, food_records, med_records
from app.services.food import suggest_tags
from app.services.logs import upsert_log
from app.services.symptoms import list_tracked
from app.services.users import get_or_create_dev_user, update_user

DAYS = 14
# Two days left unlogged, so the Trends charts show what gaps look like.
SKIPPED_DAYS_AGO = {4, 9}


class AlreadyHasLogsError(Exception):
    """Seeding would mix synthetic logs with ones already there."""


class AlreadyHasDataError(Exception):
    """Seeding would mix synthetic cycles, meds or meals with ones already there."""


# (meal type, typical time, descriptions). Plain descriptions; tags come from the
# same keyword rules the app uses, so the seed shows what real suggestions look like.
MEALS = [
    (
        "breakfast",
        time(8, 15),
        [
            "oats with berries",
            "paneer paratha and chai",
            "two eggs and toast",
            "poha and chai",
            "greek yogurt and apple",
        ],
    ),
    (
        "lunch",
        time(13, 0),
        ["dal rice and sabzi", "chicken salad", "paneer wrap", "rajma chawal", "tofu noodle bowl"],
    ),
    (
        "dinner",
        time(19, 45),
        [
            "roti, dal and sabzi",
            "salmon with brown rice",
            "pasta with veggies",
            "chana masala and rice",
            "khichdi and curd",
        ],
    ),
    ("snack", time(16, 30), ["chai and biscuits", "apple", "roasted chana", "chocolate", "samosa"]),
]


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


def seed_cycles_meds_food(
    db: Session, user: User, today: date, rng: random.Random
) -> dict[str, int]:
    """Three irregular periods, three meds/supplements with doses, and two weeks of meals."""
    for model in (Cycle, Medication, Meal):
        existing = db.scalar(select(func.count()).where(model.user_id == user.id))
        if existing:
            raise AlreadyHasDataError(f"user already has {existing} {model.__tablename__}")
    ago = lambda n: today - timedelta(days=n)  # noqa: E731

    # Cycles of 38 and 49 days: irregular on purpose, with no 28-day pattern.
    for start, length in [(120, 5), (82, 4), (33, 5)]:
        cycle_records.create_cycle(
            db, user, start_date=ago(start), end_date=ago(start - length + 1), notes=None
        )

    levo = med_records.create_med(
        db, user, name="Levothyroxine", kind="medication", dose=Decimal(50),
        dose_unit="mcg", frequency="daily", start_date=ago(90),
    )  # fmt: skip
    levo = med_records.change_dose(
        db, user, levo, dose=Decimal(75), dose_unit=None, effective_date=ago(20)
    )
    vit_d = med_records.create_med(
        db, user, name="Vitamin D", kind="supplement", dose=Decimal(1000),
        dose_unit="IU", frequency="daily", start_date=ago(60),
    )  # fmt: skip
    inositol = med_records.create_med(
        db, user, name="Inositol", kind="supplement", dose=Decimal(2),
        dose_unit="g", frequency="daily", start_date=ago(10),
    )  # fmt: skip

    doses = 0
    for days_ago in range(13, 0, -1):  # up to yesterday, so today is left to tick off
        day = ago(days_ago)
        for med in (levo, vit_d, inositol):
            if day < med.start_date:
                continue
            roll = rng.random()
            if roll < 0.08:
                continue  # left unmarked
            med_records.upsert_dose(
                db, user, med, day, taken=roll >= 0.18,
                time_taken=time(8, rng.choice([0, 10, 20, 30])) if roll >= 0.18 else None,
                notes=None,
            )  # fmt: skip
            doses += 1

    meals = 0
    for days_ago in range(DAYS - 1, 0, -1):  # up to yesterday: today is yours to log
        for meal_type, usual, options in MEALS:
            if meal_type == "snack" and rng.random() < 0.4:
                continue
            description = rng.choice(options)
            meal_time = usual
            if meal_type == "snack" and rng.random() < 0.3:
                meal_time = time(21, 40)  # a late snack, so late_night shows up
            food_records.create_meal(
                db, user,
                {
                    "date": ago(days_ago), "time": meal_time, "meal_type": meal_type,
                    "description": description, "tags": suggest_tags(description),
                },
            )  # fmt: skip
            meals += 1

    return {"cycles": 3, "meds": 4, "doses": doses, "meals": meals}


def reset(db: Session, user: User) -> None:
    """Delete ALL of the user's logs, cycles, meds (and doses), meals and custom tags."""
    for model in (DailyLog, Cycle, Medication, Meal, UserFoodTag):
        db.execute(delete(model).where(model.user_id == user.id))
    db.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--reset", action="store_true", help="delete ALL of the dev user's data before seeding"
    )
    args = parser.parse_args()

    with SessionLocal() as db:
        user = get_or_create_dev_user(db)
        if args.reset:
            reset(db, user)
            print("Deleted all of the dev user's logs, cycles, meds, meals and custom tags.")
        rng = random.Random(42)
        try:
            written = seed_two_weeks(db, user, date.today(), rng)
            print(f"Wrote {written} synthetic logs for the last {DAYS} days.")
        except AlreadyHasLogsError as e:
            print(f"Skipped logs: the dev {e}.")
        try:
            counts = seed_cycles_meds_food(db, user, date.today(), rng)
            print("Wrote " + ", ".join(f"{n} {what}" for what, n in counts.items()) + ".")
        except AlreadyHasDataError as e:
            print(f"Skipped cycles, meds and meals: the dev {e}.")


if __name__ == "__main__":
    main()
