"""Request and response shapes for the API (Pydantic v2)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

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


Rating = Annotated[int, Field(ge=1, le=5)]
Severity = Annotated[int, Field(ge=1, le=3)]


class LogSymptomIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symptom: SymptomName
    severity: Severity


class LogIn(BaseModel):
    """The whole log for one day. PUT replaces it: a field left out is cleared."""

    model_config = ConfigDict(extra="forbid")

    energy: Rating | None = None
    mood: Rating | None = None
    sleep_hours: Annotated[Decimal, Field(ge=0, le=24, decimal_places=1)] | None = None
    weight: Annotated[Decimal, Field(gt=0, le=1000)] | None = None
    notes: Annotated[str, StringConstraints(max_length=2000)] | None = None
    symptoms: list[LogSymptomIn] = []

    @field_validator("symptoms")
    @classmethod
    def no_duplicate_symptoms(cls, symptoms: list[LogSymptomIn]) -> list[LogSymptomIn]:
        names = [s.symptom for s in symptoms]
        if len(names) != len(set(names)):
            raise ValueError("each symptom can only appear once per day")
        return symptoms


class LogSymptomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symptom: str
    severity: int


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    energy: int | None
    mood: int | None
    # float, not Decimal: Pydantic would send a Decimal as a JSON string.
    sleep_hours: float | None
    weight: float | None
    notes: str | None
    symptoms: list[LogSymptomOut]
    updated_at: datetime
