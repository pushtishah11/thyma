from fastapi import APIRouter

from app.deps import CurrentUser, DbSession
from app.schemas import MeOut, MePatch
from app.services.users import update_user

router = APIRouter()


@router.get("/me", response_model=MeOut)
def get_me(user: CurrentUser) -> MeOut:
    return MeOut.model_validate(user)


@router.patch("/me", response_model=MeOut)
def patch_me(body: MePatch, db: DbSession, user: CurrentUser) -> MeOut:
    update_user(db, user, **body.model_dump(exclude_none=True))
    return MeOut.model_validate(user)
