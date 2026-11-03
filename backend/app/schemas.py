"""Request and response shapes for the API (Pydantic v2)."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

from app.services.symptoms import normalize_symptom

Condition = Literal["pcos", "thyroid"]

# Trimmed, lowercased, 1-40 characters. Validation runs on the cleaned value.
SymptomName = Annotated[
    str,
    AfterValidator(normalize_symptom),
    StringConstraints(min_length=1, max_length=40),
]


class HealthOut(BaseModel):
    status: Literal["ok", "error"]
    db: Literal["ok", "error"]


class MeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    conditions: list[Condition]
    track_cycles: bool
    track_weight: bool
    ai_consent_at: datetime | None
    created_at: datetime


class MePatch(BaseModel):
    """Only the fields that are sent get changed."""

    model_config = ConfigDict(extra="forbid")

    conditions: list[Condition] | None = None
    track_cycles: bool | None = None
    track_weight: bool | None = None
    # true records consent now; false withdraws it.
    ai_consent: bool | None = None


class TrackedSymptomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symptom: str
    position: int
    active: bool


class TrackedSymptomCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptom: SymptomName


class TrackedSymptomPatch(BaseModel):
    """Reorder or hide a chip. Renaming isn't allowed: it would split its history."""

    model_config = ConfigDict(extra="forbid")

    position: Annotated[int, Field(ge=0)] | None = None
    active: bool | None = None
