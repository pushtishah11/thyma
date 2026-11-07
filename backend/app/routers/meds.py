import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.models import Medication, User
from app.schemas import (
    AdherenceOut,
    ChangeDose,
    DayDoseOut,
    DoseIn,
    MedCreate,
    MedOut,
    MedPatch,
)
from app.services import med_records

router = APIRouter()


def _get_or_404(db: Session, user: User, med_id: uuid.UUID) -> Medication:
    med = med_records.get_med(db, user, med_id)
    if med is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication or supplement not found")
    return med


def _rule_error(e: med_records.MedRuleError) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(e))


@router.get("/meds", response_model=list[MedOut])
def list_meds(db: DbSession, user: CurrentUser) -> list[MedOut]:
    return [MedOut.model_validate(m) for m in med_records.list_meds(db, user)]


@router.post("/meds", response_model=MedOut, status_code=status.HTTP_201_CREATED)
def create_med(body: MedCreate, db: DbSession, user: CurrentUser) -> MedOut:
    return MedOut.model_validate(med_records.create_med(db, user, **body.model_dump()))


@router.patch("/meds/{med_id}", response_model=MedOut)
def update_med(med_id: uuid.UUID, body: MedPatch, db: DbSession, user: CurrentUser) -> MedOut:
    med = _get_or_404(db, user, med_id)
    try:
        med = med_records.update_med(db, med, body.model_dump(exclude_unset=True))
    except med_records.MedRuleError as e:
        raise _rule_error(e) from None
    return MedOut.model_validate(med)


@router.delete("/meds/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_med(med_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    med_records.delete_med(db, _get_or_404(db, user, med_id))


@router.post(
    "/meds/{med_id}/change-dose", response_model=MedOut, status_code=status.HTTP_201_CREATED
)
def change_dose(med_id: uuid.UUID, body: ChangeDose, db: DbSession, user: CurrentUser) -> MedOut:
    med = _get_or_404(db, user, med_id)
    try:
        new = med_records.change_dose(
            db,
            user,
            med,
            dose=body.dose,
            dose_unit=body.dose_unit,
            effective_date=body.effective_date,
        )
    except med_records.MedRuleError as e:
        raise _rule_error(e) from None
    return MedOut.model_validate(new)


@router.get("/meds/{med_id}/adherence", response_model=AdherenceOut)
def get_adherence(
    med_id: uuid.UUID, start: date, end: date, db: DbSession, user: CurrentUser
) -> AdherenceOut:
    if start > end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "start must be on or before end")
    med = _get_or_404(db, user, med_id)
    return AdherenceOut.model_validate(med_records.adherence_for(db, med, start, end))


@router.get("/doses", response_model=list[DayDoseOut])
def doses_for_day(
    day: Annotated[date, Query(alias="date")], db: DbSession, user: CurrentUser
) -> list[DayDoseOut]:
    return [
        DayDoseOut(
            medication=MedOut.model_validate(med),
            taken=dose.taken if dose else None,
            time_taken=dose.time_taken if dose else None,
            notes=dose.notes if dose else None,
        )
        for med, dose in med_records.doses_for_day(db, user, day)
    ]


@router.put("/doses/{med_id}/{day}", response_model=DayDoseOut)
def put_dose(
    med_id: uuid.UUID, day: date, body: DoseIn, db: DbSession, user: CurrentUser
) -> DayDoseOut:
    med = _get_or_404(db, user, med_id)
    try:
        dose = med_records.upsert_dose(
            db, user, med, day, taken=body.taken, time_taken=body.time_taken, notes=body.notes
        )
    except med_records.MedRuleError as e:
        raise _rule_error(e) from None
    return DayDoseOut(
        medication=MedOut.model_validate(med),
        taken=dose.taken,
        time_taken=dose.time_taken,
        notes=dose.notes,
    )
