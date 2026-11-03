from datetime import date

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession
from app.schemas import LogIn, LogOut
from app.services import logs

router = APIRouter(prefix="/logs")


@router.get("", response_model=list[LogOut])
def list_logs(start: date, end: date, db: DbSession, user: CurrentUser) -> list[LogOut]:
    if start > end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "start must be on or before end")
    return [LogOut.model_validate(log) for log in logs.list_logs(db, user, start, end)]


@router.put("/{day}", response_model=LogOut)
def put_log(day: date, body: LogIn, db: DbSession, user: CurrentUser) -> LogOut:
    try:
        log = logs.upsert_log(
            db,
            user,
            day,
            energy=body.energy,
            mood=body.mood,
            sleep_hours=body.sleep_hours,
            weight=body.weight,
            notes=body.notes,
            symptoms=[(s.symptom, s.severity) for s in body.symptoms],
        )
    except logs.WeightNotTrackedError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Weight tracking is off. Turn it on in settings to log weight.",
        ) from None
    return LogOut.model_validate(log)


@router.delete("/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(day: date, db: DbSession, user: CurrentUser) -> None:
    if not logs.delete_log(db, user, day):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No log for that date")
