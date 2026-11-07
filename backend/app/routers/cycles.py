import uuid
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.models import Cycle, User
from app.schemas import CycleCreate, CycleOut, CyclePatch, CycleSummaryOut
from app.services import cycle_records
from app.services.cycles import DEFAULT_GAP_THRESHOLD

router = APIRouter(prefix="/cycles")


def _latest_allowed_day() -> date:
    # The server runs on UTC, so allow one day ahead for people east of UTC
    # whose "today" is already tomorrow on the server.
    return date.today() + timedelta(days=1)


def _not_in_future(day: date | None) -> None:
    if day is not None and day > _latest_allowed_day():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Dates can't be in the future")


def _get_or_404(db: Session, user: User, cycle_id: uuid.UUID) -> Cycle:
    cycle = cycle_records.get_cycle(db, user, cycle_id)
    if cycle is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cycle not found")
    return cycle


@router.get("", response_model=list[CycleOut])
def list_cycles(db: DbSession, user: CurrentUser) -> list[CycleOut]:
    return [CycleOut.model_validate(c) for c in cycle_records.list_cycles(db, user)]


# Declared before /{cycle_id} so "summary" isn't read as an id.
@router.get("/summary", response_model=CycleSummaryOut)
def cycle_summary(
    db: DbSession,
    user: CurrentUser,
    gap_threshold: Annotated[int, Query(ge=1, le=365)] = DEFAULT_GAP_THRESHOLD,
    today: date | None = None,
) -> CycleSummaryOut:
    # The app sends the user's local date; the server's own date (UTC) is the fallback.
    summary = cycle_records.cycle_summary(db, user, today or date.today(), gap_threshold)
    return CycleSummaryOut.model_validate(summary)


@router.post("", response_model=CycleOut, status_code=status.HTTP_201_CREATED)
def create_cycle(body: CycleCreate, db: DbSession, user: CurrentUser) -> CycleOut:
    _not_in_future(body.start_date)
    _not_in_future(body.end_date)
    try:
        cycle = cycle_records.create_cycle(
            db, user, start_date=body.start_date, end_date=body.end_date, notes=body.notes
        )
    except cycle_records.CycleConflictError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from None
    return CycleOut.model_validate(cycle)


@router.patch("/{cycle_id}", response_model=CycleOut)
def update_cycle(
    cycle_id: uuid.UUID, body: CyclePatch, db: DbSession, user: CurrentUser
) -> CycleOut:
    cycle = _get_or_404(db, user, cycle_id)
    changes = body.model_dump(exclude_unset=True)
    _not_in_future(changes.get("start_date"))
    _not_in_future(changes.get("end_date"))
    start = changes.get("start_date", cycle.start_date)
    end = changes["end_date"] if "end_date" in changes else cycle.end_date
    if end is not None and end < start:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "end_date can't be before start_date"
        )
    try:
        cycle = cycle_records.update_cycle(db, user, cycle, changes)
    except cycle_records.CycleConflictError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from None
    return CycleOut.model_validate(cycle)


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(cycle_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    cycle_records.delete_cycle(db, _get_or_404(db, user, cycle_id))
