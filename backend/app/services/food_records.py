"""Reading and writing meals and food tags. The tag rules live in food.py (pure)."""

import uuid
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import FoodTag, Meal, User, UserFoodTag
from app.services.food import CATALOG, LATE_NIGHT, suggest_tags, tag_key, tidy_tags


class FoodRuleError(Exception):
    """The request breaks a rule about meals or tags (the message says which)."""


class TagExistsError(FoodRuleError):
    """A tag with that key already exists."""


def custom_tags(db: Session, user: User) -> list[UserFoodTag]:
    return list(
        db.scalars(
            select(UserFoodTag).where(UserFoodTag.user_id == user.id).order_by(UserFoodTag.key)
        )
    )


def all_tags(db: Session, user: User) -> list[tuple[str, str, bool]]:
    """(key, display_name, custom) for the catalog, in order, then the user's own tags."""
    builtin = {t.key: t.display_name for t in db.scalars(select(FoodTag))}
    ordered = [(k, builtin[k], False) for k in CATALOG if k in builtin]
    return ordered + [(t.key, t.display_name, True) for t in custom_tags(db, user)]


def add_custom_tag(db: Session, user: User, display_name: str) -> UserFoodTag:
    key = tag_key(display_name)
    if not key:
        raise FoodRuleError("A tag needs at least one letter or number")
    if key in CATALOG or any(t.key == key for t in custom_tags(db, user)):
        raise TagExistsError(f"There's already a '{key}' tag")
    tag = UserFoodTag(user_id=user.id, key=key, display_name=display_name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def delete_custom_tag(db: Session, user: User, key: str) -> bool:
    """Delete one of the user's own tags, and take it off their meals. False if not found."""
    tag = db.scalar(
        select(UserFoodTag).where(UserFoodTag.user_id == user.id, UserFoodTag.key == key)
    )
    if tag is None:
        return False
    db.execute(
        update(Meal).where(Meal.user_id == user.id).values(tags=func.array_remove(Meal.tags, key))
    )
    db.delete(tag)
    db.commit()
    return True


def suggest_for(db: Session, user: User, description: str) -> list[str]:
    custom = {t.key: t.display_name for t in custom_tags(db, user)}
    return suggest_tags(description, custom)


def _clean_tags(
    db: Session, user: User, tags: list[str], meal: Meal | None, changes: dict
) -> list[str]:
    meal_time = changes["time"] if "time" in changes else (meal.time if meal else None)
    tidy = tidy_tags(tags, meal_time)
    allowed = set(CATALOG) | {t.key for t in custom_tags(db, user)}
    unknown = [t for t in tidy if t not in allowed]
    if unknown:
        raise FoodRuleError(f"Unknown tag: {', '.join(unknown)}")
    return tidy


def list_meals(db: Session, user: User, start: date, end: date) -> list[Meal]:
    """Meals from start to end, by date then time (meals with no time last in their day)."""
    return list(
        db.scalars(
            select(Meal)
            .where(Meal.user_id == user.id, Meal.date >= start, Meal.date <= end)
            .order_by(Meal.date, Meal.time.asc().nulls_last(), Meal.created_at)
        )
    )


def get_meal(db: Session, user: User, meal_id: uuid.UUID) -> Meal | None:
    return db.scalar(select(Meal).where(Meal.user_id == user.id, Meal.id == meal_id))


def create_meal(db: Session, user: User, fields: dict) -> Meal:
    fields = {**fields, "tags": _clean_tags(db, user, fields["tags"], None, fields)}
    meal = Meal(user_id=user.id, **fields)
    db.add(meal)
    db.commit()
    db.refresh(meal)
    return meal


def update_meal(db: Session, user: User, meal: Meal, changes: dict) -> Meal:
    # The tags are re-checked whenever they or the time change, so late_night stays right.
    if "tags" in changes or "time" in changes:
        tags = changes.get("tags", [t for t in meal.tags if t != LATE_NIGHT])
        changes = {**changes, "tags": _clean_tags(db, user, tags, meal, changes)}
    for field, value in changes.items():
        setattr(meal, field, value)
    db.commit()
    db.refresh(meal)
    return meal


def delete_meal(db: Session, meal: Meal) -> None:
    db.delete(meal)
    db.commit()
