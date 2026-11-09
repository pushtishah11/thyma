"""Lab values: parsing what's printed on a report, plus reading and writing results.

`parse_value` is pure. M4's extraction validator reuses it, so a value typed by hand
and a value read off a report are parsed by exactly the same rule.
"""

import re
import uuid
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LabResult, Marker, User

CATEGORY_ORDER = ("thyroid", "androgens", "reproductive", "metabolic", "other")

# An optional < > ≤ ≥ sign, then a number like 2.1, .5 or 1,200.
_VALUE = re.compile(r"^\s*([<>≤≥]=?)?\s*(\d{1,3}(?:,\d{3})+|\d*\.?\d+)\s*$")


def parse_value(text: str) -> Decimal | None:
    """The number in a printed value ("2.1", "<0.5", "> 90", "1,200"), or None.

    A "<" or ">" sign is kept in the text (value_text), never dropped silently: the
    number alone would claim an exactness the report doesn't.
    """
    match = _VALUE.match(text)
    if not match:
        return None
    try:
        return Decimal(match.group(2).replace(",", ""))
    except InvalidOperation:
        return None


def list_markers(db: Session) -> list[Marker]:
    markers = db.scalars(select(Marker)).all()
    return sorted(markers, key=lambda m: (CATEGORY_ORDER.index(m.category), m.position))


def get_marker(db: Session, key: str) -> Marker | None:
    return db.get(Marker, key)


def list_results(db: Session, user: User, marker_key: str | None = None) -> list[LabResult]:
    """Confirmed results only, oldest first. Unconfirmed rows are still awaiting review."""
    query = select(LabResult).where(LabResult.user_id == user.id, LabResult.confirmed.is_(True))
    if marker_key is not None:
        query = query.where(LabResult.marker_key == marker_key)
    return list(db.scalars(query.order_by(LabResult.date, LabResult.created_at)))


def get_result(db: Session, user: User, result_id: uuid.UUID) -> LabResult | None:
    return db.scalar(
        select(LabResult).where(LabResult.user_id == user.id, LabResult.id == result_id)
    )


def create_result(db: Session, user: User, fields: dict) -> LabResult:
    """A hand-entered result. It's confirmed straight away: the user typed it themselves."""
    row = LabResult(user_id=user.id, document_id=None, confirmed=True, **fields)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_result(db: Session, row: LabResult, changes: dict) -> LabResult:
    for field, value in changes.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


def delete_result(db: Session, row: LabResult) -> None:
    db.delete(row)
    db.commit()
