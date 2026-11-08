"""The marker catalog seeded by migration 0006, and the database rules for lab results."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import LabResult, Marker, User

SPEC_CATALOG = {
    "thyroid": [
        "tsh", "free_t4", "free_t3", "total_t3", "tpo_antibodies", "thyroglobulin_antibodies",
    ],
    "androgens": ["total_testosterone", "free_testosterone", "dhea_s", "shbg", "androstenedione"],
    "reproductive": ["lh", "fsh", "amh", "estradiol", "progesterone", "prolactin"],
    "metabolic": [
        "fasting_glucose", "fasting_insulin", "hba1c", "total_cholesterol", "ldl", "hdl",
        "triglycerides",
    ],
    "other": ["vitamin_d", "ferritin", "b12"],
}  # fmt: skip


def test_catalog_matches_the_spec(db: Session) -> None:
    markers = db.scalars(select(Marker).order_by(Marker.position)).all()

    by_category: dict[str, list[str]] = {}
    for m in markers:
        by_category.setdefault(m.category, []).append(m.key)
    assert by_category == SPEC_CATALOG


def test_aliases_are_lowercase_and_include_the_key_name(db: Session) -> None:
    for m in db.scalars(select(Marker)):
        assert m.aliases, m.key
        assert all(a == a.lower().strip() for a in m.aliases), m.key
        assert m.display_name.lower() in m.aliases or m.key.replace("_", " ") in m.aliases


def result(user: User, **fields: object) -> LabResult:
    base = {
        "user_id": user.id,
        "date": date(2026, 3, 1),
        "marker_key": "tsh",
        "raw_marker": "TSH",
        "value": Decimal("2.1"),
        "value_text": "2.1",
        "unit": "mIU/L",
    }
    return LabResult(**{**base, **fields})


def test_inverted_range_is_rejected(db: Session, user: User) -> None:
    db.add(result(user, ref_low=Decimal("4.5"), ref_high=Decimal("0.45")))

    with pytest.raises(IntegrityError, match="lab_results_ref_range_ordered"):
        db.flush()


def test_unknown_marker_key_is_rejected(db: Session, user: User) -> None:
    db.add(result(user, marker_key="made_up"))

    with pytest.raises(IntegrityError):
        db.flush()


def test_unmatched_marker_is_allowed_and_unconfirmed_by_default(db: Session, user: User) -> None:
    row = result(user, marker_key=None, raw_marker="Some new test")
    db.add(row)
    db.flush()

    assert row.confirmed is False
