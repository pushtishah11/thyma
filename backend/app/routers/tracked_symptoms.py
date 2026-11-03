import uuid

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.models import TrackedSymptom, User
from app.schemas import TrackedSymptomCreate, TrackedSymptomOut, TrackedSymptomPatch
from app.services import symptoms

router = APIRouter(prefix="/tracked-symptoms")


def _get_or_404(db: Session, user: User, symptom_id: uuid.UUID) -> TrackedSymptom:
    tracked = symptoms.get_tracked(db, user, symptom_id)
    # Another user's chip gets the same 404 as a missing one, so ids can't be probed.
    if tracked is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tracked symptom not found")
    return tracked


@router.get("", response_model=list[TrackedSymptomOut])
def list_tracked_symptoms(
    db: DbSession, user: CurrentUser, include_inactive: bool = False
) -> list[TrackedSymptomOut]:
    rows = symptoms.list_tracked(db, user, include_inactive=include_inactive)
    return [TrackedSymptomOut.model_validate(row) for row in rows]


@router.post("", response_model=TrackedSymptomOut, status_code=status.HTTP_201_CREATED)
def add_tracked_symptom(
    body: TrackedSymptomCreate, db: DbSession, user: CurrentUser, response: Response
) -> TrackedSymptomOut:
    existing = symptoms.find_by_name(db, user, body.symptom)
    if existing is not None and existing.active:
        raise HTTPException(status.HTTP_409_CONFLICT, f"'{body.symptom}' is already tracked")
    if existing is not None:
        # Re-adding a hidden chip brings it back instead of making a duplicate.
        existing.active = True
        db.commit()
        response.status_code = status.HTTP_200_OK
        return TrackedSymptomOut.model_validate(existing)
    tracked = symptoms.add_tracked(db, user, body.symptom)
    db.commit()
    return TrackedSymptomOut.model_validate(tracked)


@router.patch("/{symptom_id}", response_model=TrackedSymptomOut)
def update_tracked_symptom(
    symptom_id: uuid.UUID, body: TrackedSymptomPatch, db: DbSession, user: CurrentUser
) -> TrackedSymptomOut:
    tracked = _get_or_404(db, user, symptom_id)
    if body.position is not None:
        tracked.position = body.position
    if body.active is not None:
        tracked.active = body.active
    db.commit()
    return TrackedSymptomOut.model_validate(tracked)


@router.delete("/{symptom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracked_symptom(symptom_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    """Removes the chip only. Past logs of this symptom are kept."""
    db.delete(_get_or_404(db, user, symptom_id))
    db.commit()
