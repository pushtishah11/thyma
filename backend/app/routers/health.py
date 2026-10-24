import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession
from app.schemas import HealthOut

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health(db: DbSession, response: Response) -> HealthOut:
    """Is the API up, and can it reach Postgres?

    Returns 503 when the database is unreachable, so uptime checks and Docker
    healthchecks see a failure from the status code alone.
    """
    try:
        db.execute(text("select 1"))
    except SQLAlchemyError:
        logger.warning("health check: database unreachable", exc_info=True)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthOut(status="error", db="error")
    return HealthOut(status="ok", db="ok")
