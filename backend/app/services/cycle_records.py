"""Reading and writing a user's cycles. The math itself lives in cycles.py (pure)."""

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cycle, User
from app.services.cycles import CycleIn, CycleSummary, find_conflict, summarize_cycles


class CycleConflictError(Exception):
    """The period would share a start date with, or overlap, another one."""


def list_cycles(db: Session, user: User) -> list[Cycle]:
    """All of the user's periods, newest first."""
    return list(
        db.scalars(select(Cycle).where(Cycle.user_id == user.id).order_by(Cycle.start_date.desc()))
    )


def get_cycle(db: Session, user: User, cycle_id: uuid.UUID) -> Cycle | None:
    return db.scalar(select(Cycle).where(Cycle.user_id == user.id, Cycle.id == cycle_id))


def _check(db: Session, user: User, candidate: CycleIn, ignore_id: uuid.UUID | None) -> None:
    others = [CycleIn(c.start_date, c.end_date) for c in list_cycles(db, user) if c.id != ignore_id]
    problem = find_conflict(others, candidate)
    if problem:
        raise CycleConflictError(problem)


def create_cycle(
    db: Session, user: User, *, start_date: date, end_date: date | None, notes: str | None
) -> Cycle:
    _check(db, user, CycleIn(start_date, end_date), ignore_id=None)
    cycle = Cycle(user_id=user.id, start_date=start_date, end_date=end_date, notes=notes)
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def update_cycle(db: Session, user: User, cycle: Cycle, changes: dict) -> Cycle:
    """Apply only the fields that were sent. Sending end_date: null clears it."""
    start = changes.get("start_date", cycle.start_date)
    end = changes["end_date"] if "end_date" in changes else cycle.end_date
    _check(db, user, CycleIn(start, end), ignore_id=cycle.id)
    for field, value in changes.items():
        setattr(cycle, field, value)
    db.commit()
    db.refresh(cycle)
    return cycle


def delete_cycle(db: Session, cycle: Cycle) -> None:
    db.delete(cycle)
    db.commit()


def cycle_summary(db: Session, user: User, today: date, gap_threshold: int) -> CycleSummary:
    cycles = [CycleIn(c.start_date, c.end_date) for c in list_cycles(db, user)]
    return summarize_cycles(cycles, today, gap_threshold)
