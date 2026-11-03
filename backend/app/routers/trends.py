from datetime import date

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DbSession
from app.schemas import TrendsOut
from app.services import logs
from app.services.trends import MAX_RANGE_DAYS, compute_trends

router = APIRouter(prefix="/trends")


@router.get("", response_model=TrendsOut)
def get_trends(start: date, end: date, db: DbSession, user: CurrentUser) -> TrendsOut:
    if start > end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "start must be on or before end")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"range can be at most {MAX_RANGE_DAYS} days"
        )
    trends = compute_trends(logs.list_logs(db, user, start, end), start, end)
    return TrendsOut.model_validate(trends)
