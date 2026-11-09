import uuid
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.models import LabResult, User
from app.schemas import LabCreate, LabOut, LabPatch, MarkerOut
from app.services import labs
from app.services.flags import flag

router = APIRouter()


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail)


def _to_out(row: LabResult) -> LabOut:
    return LabOut(
        id=row.id,
        date=row.date,
        marker_key=row.marker_key,
        raw_marker=row.raw_marker,
        value=float(row.value),
        value_text=row.value_text,
        unit=row.unit,
        ref_low=float(row.ref_low) if row.ref_low is not None else None,
        ref_high=float(row.ref_high) if row.ref_high is not None else None,
        ref_text=row.ref_text,
        flag=flag(row.value, row.ref_low, row.ref_high, row.value_text),
        from_report=row.document_id is not None,
    )


def _check(db: Session, fields: dict) -> dict:
    """Shared rules for create and update. Returns the extra fields to store."""
    extra: dict = {}
    if "date" in fields and fields["date"] > date.today() + timedelta(days=1):
        raise _unprocessable("Dates can't be in the future")
    if "marker_key" in fields:
        marker = labs.get_marker(db, fields["marker_key"])
        if marker is None:
            raise _unprocessable(f"Unknown marker: {fields['marker_key']}")
        extra["raw_marker"] = marker.display_name
    if "value_text" in fields:
        value = labs.parse_value(fields["value_text"])
        if value is None:
            raise _unprocessable("The value should be a number, like 2.1, <0.5 or >90")
        extra["value"] = value
    return extra


def _check_range(low: Decimal | None, high: Decimal | None) -> None:
    if low is not None and high is not None and low > high:
        raise _unprocessable("The low end of the range can't be above the high end")


def _get_or_404(db: Session, user: User, result_id: uuid.UUID) -> LabResult:
    row = labs.get_result(db, user, result_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lab result not found")
    return row


@router.get("/markers", response_model=list[MarkerOut])
def list_markers(db: DbSession) -> list[MarkerOut]:
    return [MarkerOut.model_validate(m) for m in labs.list_markers(db)]


@router.get("/labs", response_model=list[LabOut])
def list_labs(db: DbSession, user: CurrentUser, marker_key: str | None = None) -> list[LabOut]:
    """Confirmed results, oldest first, each with its flag against its own report's range."""
    return [_to_out(r) for r in labs.list_results(db, user, marker_key)]


@router.post("/labs", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def create_lab(body: LabCreate, db: DbSession, user: CurrentUser) -> LabOut:
    fields = body.model_dump()
    extra = _check(db, fields)
    _check_range(body.ref_low, body.ref_high)
    return _to_out(labs.create_result(db, user, {**fields, **extra}))


@router.patch("/labs/{result_id}", response_model=LabOut)
def update_lab(result_id: uuid.UUID, body: LabPatch, db: DbSession, user: CurrentUser) -> LabOut:
    row = _get_or_404(db, user, result_id)
    changes = body.model_dump(exclude_unset=True)
    extra = _check(db, changes)
    _check_range(
        changes["ref_low"] if "ref_low" in changes else row.ref_low,
        changes["ref_high"] if "ref_high" in changes else row.ref_high,
    )
    return _to_out(labs.update_result(db, row, {**changes, **extra}))


@router.delete("/labs/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab(result_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    labs.delete_result(db, _get_or_404(db, user, result_id))
