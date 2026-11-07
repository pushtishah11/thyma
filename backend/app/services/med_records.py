"""Reading and writing a user's meds, supplements and doses. Math lives in meds.py."""

import uuid
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MedDose, Medication, User
from app.services.meds import Adherence, adherence, is_active_on


class MedRuleError(Exception):
    """The request breaks a rule about meds (the message says which)."""


def list_meds(db: Session, user: User) -> list[Medication]:
    """Current ones first (by name), then stopped ones (most recently stopped first)."""
    return list(
        db.scalars(
            select(Medication)
            .where(Medication.user_id == user.id)
            .order_by(
                Medication.end_date.is_not(None),
                Medication.end_date.desc(),
                Medication.name,
                Medication.start_date.desc(),
            )
        )
    )


def get_med(db: Session, user: User, med_id: uuid.UUID) -> Medication | None:
    return db.scalar(
        select(Medication).where(Medication.user_id == user.id, Medication.id == med_id)
    )


def create_med(db: Session, user: User, **fields: object) -> Medication:
    med = Medication(user_id=user.id, **fields)
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


def update_med(db: Session, med: Medication, changes: dict) -> Medication:
    start = changes.get("start_date", med.start_date)
    end = changes["end_date"] if "end_date" in changes else med.end_date
    if end is not None and end < start:
        raise MedRuleError("end_date can't be before start_date")
    for field, value in changes.items():
        setattr(med, field, value)
    db.commit()
    db.refresh(med)
    return med


def delete_med(db: Session, med: Medication) -> None:
    db.delete(med)  # its doses go with it (ON DELETE CASCADE)
    db.commit()


def change_dose(
    db: Session,
    user: User,
    med: Medication,
    *,
    dose: Decimal,
    dose_unit: str | None,
    effective_date: date,
) -> Medication:
    """End the current row the day before effective_date and start a new one at the new dose."""
    if med.end_date is not None:
        raise MedRuleError("This one has already been stopped, so its dose can't change")
    if effective_date <= med.start_date:
        raise MedRuleError("The new dose has to start after the current one started")

    med.end_date = effective_date - timedelta(days=1)
    new = Medication(
        user_id=user.id,
        name=med.name,
        kind=med.kind,
        dose=dose,
        dose_unit=dose_unit if dose_unit is not None else med.dose_unit,
        frequency=med.frequency,
        start_date=effective_date,
        notes=med.notes,
    )
    db.add(new)
    db.flush()
    # Doses already recorded from the effective date on were the new dose.
    for d in db.scalars(
        select(MedDose).where(MedDose.medication_id == med.id, MedDose.date >= effective_date)
    ):
        d.medication_id = new.id
    db.commit()
    db.refresh(new)
    return new


def doses_for_day(db: Session, user: User, day: date) -> list[tuple[Medication, MedDose | None]]:
    """Every med active on `day`, with that day's dose record if there is one."""
    meds = [m for m in list_meds(db, user) if is_active_on(m.start_date, m.end_date, day)]
    records = {
        d.medication_id: d
        for d in db.scalars(select(MedDose).where(MedDose.user_id == user.id, MedDose.date == day))
    }
    return [(m, records.get(m.id)) for m in meds]


def upsert_dose(
    db: Session,
    user: User,
    med: Medication,
    day: date,
    *,
    taken: bool,
    time_taken: time | None,
    notes: str | None,
) -> MedDose:
    if not is_active_on(med.start_date, med.end_date, day):
        raise MedRuleError(f"{med.name} wasn't active on {day.isoformat()}")
    dose = db.scalar(select(MedDose).where(MedDose.medication_id == med.id, MedDose.date == day))
    if dose is None:
        dose = MedDose(user_id=user.id, medication_id=med.id, date=day, taken=taken)
        db.add(dose)
    dose.taken = taken
    dose.time_taken = time_taken
    dose.notes = notes
    db.commit()
    db.refresh(dose)
    return dose


def adherence_for(db: Session, med: Medication, start: date, end: date) -> Adherence:
    doses = db.scalars(
        select(MedDose).where(
            MedDose.medication_id == med.id, MedDose.date >= start, MedDose.date <= end
        )
    )
    return adherence(start, end, med.start_date, med.end_date, [(d.date, d.taken) for d in doses])
