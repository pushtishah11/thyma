import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import CurrentUser, DbSession
from app.models import Meal, User
from app.schemas import (
    FoodTagCreate,
    FoodTagOut,
    MealCreate,
    MealOut,
    MealPatch,
    SuggestTagsIn,
    SuggestTagsOut,
)
from app.services import food_records
from app.services.food import CATALOG

router = APIRouter()

MAX_RANGE_DAYS = 366


def _get_or_404(db: Session, user: User, meal_id: uuid.UUID) -> Meal:
    meal = food_records.get_meal(db, user, meal_id)
    if meal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Meal not found")
    return meal


def _rule_error(e: food_records.FoodRuleError) -> HTTPException:
    code = (
        status.HTTP_409_CONFLICT
        if isinstance(e, food_records.TagExistsError)
        else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    return HTTPException(code, str(e))


@router.get("/meals", response_model=list[MealOut])
def list_meals(
    db: DbSession,
    user: CurrentUser,
    date: date | None = None,
    start: date | None = None,
    end: date | None = None,
) -> list[MealOut]:
    """Either ?date= for one day, or ?start=&end= for a range."""
    if date is not None and (start or end):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Use date, or start and end")
    if date is not None:
        start = end = date
    if start is None or end is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Use date, or start and end")
    if start > end:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "start must be on or before end")
    if (end - start).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"range can be at most {MAX_RANGE_DAYS} days"
        )
    return [MealOut.model_validate(m) for m in food_records.list_meals(db, user, start, end)]


@router.post("/meals", response_model=MealOut, status_code=status.HTTP_201_CREATED)
def create_meal(body: MealCreate, db: DbSession, user: CurrentUser) -> MealOut:
    try:
        meal = food_records.create_meal(db, user, body.model_dump())
    except food_records.FoodRuleError as e:
        raise _rule_error(e) from None
    return MealOut.model_validate(meal)


# Declared before /meals/{meal_id} so "suggest-tags" isn't read as an id.
@router.post("/meals/suggest-tags", response_model=SuggestTagsOut)
def suggest_tags(body: SuggestTagsIn, db: DbSession, user: CurrentUser) -> SuggestTagsOut:
    """Keyword-based suggestions (an LLM takes over in M5). The user confirms every tag."""
    return SuggestTagsOut(tags=food_records.suggest_for(db, user, body.description))


@router.patch("/meals/{meal_id}", response_model=MealOut)
def update_meal(meal_id: uuid.UUID, body: MealPatch, db: DbSession, user: CurrentUser) -> MealOut:
    meal = _get_or_404(db, user, meal_id)
    try:
        meal = food_records.update_meal(db, user, meal, body.model_dump(exclude_unset=True))
    except food_records.FoodRuleError as e:
        raise _rule_error(e) from None
    return MealOut.model_validate(meal)


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: uuid.UUID, db: DbSession, user: CurrentUser) -> None:
    food_records.delete_meal(db, _get_or_404(db, user, meal_id))


@router.get("/food-tags", response_model=list[FoodTagOut])
def list_food_tags(db: DbSession, user: CurrentUser) -> list[FoodTagOut]:
    return [
        FoodTagOut(key=k, display_name=n, custom=c) for k, n, c in food_records.all_tags(db, user)
    ]


@router.post("/food-tags", response_model=FoodTagOut, status_code=status.HTTP_201_CREATED)
def add_food_tag(body: FoodTagCreate, db: DbSession, user: CurrentUser) -> FoodTagOut:
    try:
        tag = food_records.add_custom_tag(db, user, body.display_name)
    except food_records.FoodRuleError as e:
        raise _rule_error(e) from None
    return FoodTagOut(key=tag.key, display_name=tag.display_name, custom=True)


@router.delete("/food-tags/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food_tag(key: str, db: DbSession, user: CurrentUser) -> None:
    if key in CATALOG:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Built-in tags can't be deleted")
    if not food_records.delete_custom_tag(db, user, key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tag not found")
