"""Daily logs: one per user per day, with that day's symptoms."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import DailyLog, LogSymptom, User


class WeightNotTrackedError(Exception):
    """Weight was sent, but the user hasn't turned weight tracking on."""


def list_logs(db: Session, user: User, start: date, end: date) -> list[DailyLog]:
    """Logs from start to end (both included), oldest first, with symptoms loaded."""
    return list(
        db.scalars(
            select(DailyLog)
            .where(DailyLog.user_id == user.id, DailyLog.date >= start, DailyLog.date <= end)
            .options(selectinload(DailyLog.symptoms))
            .order_by(DailyLog.date)
        )
    )


def get_log(db: Session, user: User, day: date) -> DailyLog | None:
    return db.scalar(select(DailyLog).where(DailyLog.user_id == user.id, DailyLog.date == day))


def upsert_log(
    db: Session,
    user: User,
    day: date,
    *,
    energy: int | None,
    mood: int | None,
    sleep_hours: Decimal | None,
    weight: Decimal | None,
    notes: str | None,
    symptoms: list[tuple[str, int]],
) -> DailyLog:
    """Create or fully replace the log for this day, including its symptom set."""
    if weight is not None and not user.track_weight:
        raise WeightNotTrackedError

    log = get_log(db, user, day)
    if log is None:
        log = DailyLog(user_id=user.id, date=day)
        db.add(log)

    log.energy = energy
    log.mood = mood
    log.sleep_hours = sleep_hours
    log.weight = weight
    log.notes = notes

    # Remove the old symptoms first and flush, so re-adding a symptom that was
    # already there doesn't collide with the old row on the unique constraint.
    log.symptoms.clear()
    db.flush()
    log.symptoms.extend(
        LogSymptom(user_id=user.id, symptom=name, severity=severity) for name, severity in symptoms
    )

    db.commit()
    db.refresh(log)
    return log


def delete_log(db: Session, user: User, day: date) -> bool:
    """Delete the log for this day. Returns False if there wasn't one."""
    log = get_log(db, user, day)
    if log is None:
        return False
    db.delete(log)
    db.commit()
    return True
