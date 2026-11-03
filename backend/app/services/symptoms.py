"""The user's tracked symptom list (the chips on the Today page)."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import TrackedSymptom, User

PCOS_SYMPTOMS = ["acne", "hair thinning", "excess hair growth", "cravings", "bloating", "fatigue"]
THYROID_SYMPTOMS = [
    "fatigue",
    "cold intolerance",
    "brain fog",
    "hair loss",
    "dry skin",
    "constipation",
]
EVERYONE_SYMPTOMS = ["mood swings", "headache"]


def normalize_symptom(name: str) -> str:
    """Canonical form used everywhere: trimmed, single spaces, lowercase."""
    return " ".join(name.split()).lower()


def default_symptoms(conditions: list[str]) -> list[str]:
    """Starter chips for a set of conditions, in display order, without duplicates.

    Fatigue is on both the PCOS and thyroid lists, but only appears once.
    """
    names: list[str] = []
    if "pcos" in conditions:
        names += PCOS_SYMPTOMS
    if "thyroid" in conditions:
        names += THYROID_SYMPTOMS
    names += EVERYONE_SYMPTOMS
    return list(dict.fromkeys(names))


def list_tracked(db: Session, user: User, include_inactive: bool = False) -> list[TrackedSymptom]:
    query = select(TrackedSymptom).where(TrackedSymptom.user_id == user.id)
    if not include_inactive:
        query = query.where(TrackedSymptom.active)
    return list(db.scalars(query.order_by(TrackedSymptom.position, TrackedSymptom.symptom)))


def get_tracked(db: Session, user: User, symptom_id: uuid.UUID) -> TrackedSymptom | None:
    """The chip with this id, only if it belongs to this user."""
    return db.scalar(
        select(TrackedSymptom).where(
            TrackedSymptom.id == symptom_id, TrackedSymptom.user_id == user.id
        )
    )


def find_by_name(db: Session, user: User, symptom: str) -> TrackedSymptom | None:
    return db.scalar(
        select(TrackedSymptom).where(
            TrackedSymptom.user_id == user.id, TrackedSymptom.symptom == symptom
        )
    )


def _next_position(db: Session, user: User) -> int:
    highest = db.scalar(
        select(func.max(TrackedSymptom.position)).where(TrackedSymptom.user_id == user.id)
    )
    return 0 if highest is None else highest + 1


def add_tracked(db: Session, user: User, symptom: str) -> TrackedSymptom:
    """Append a new chip at the end of the list. The caller checks it isn't tracked yet."""
    tracked = TrackedSymptom(user_id=user.id, symptom=symptom, position=_next_position(db, user))
    db.add(tracked)
    db.flush()
    return tracked


def add_default_symptoms(db: Session, user: User) -> None:
    """Add any starter chips for the user's conditions that they don't already have.

    Only ever adds. Removing a condition never deletes chips, because the user
    may have logged those symptoms, and their history stays theirs.
    """
    existing = set(
        db.scalars(select(TrackedSymptom.symptom).where(TrackedSymptom.user_id == user.id))
    )
    for name in default_symptoms(user.conditions):
        if name not in existing:
            add_tracked(db, user, name)
