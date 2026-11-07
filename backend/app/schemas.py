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
    model_validator,
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


class DayPointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    logged: bool
    energy: int | None
    mood: int | None
    sleep_hours: float | None


class SymptomTrendOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symptom: str
    days: int
    percent_of_logged_days: int
    avg_severity: float


class TrendsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start: date
    end: date
    days_in_range: int
    days_logged: int
    avg_energy: float | None
    avg_mood: float | None
    avg_sleep_hours: float | None
    daily: list[DayPointOut]
    symptoms: list[SymptomTrendOut]


Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class CycleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date
    end_date: date | None = None
    notes: Notes | None = None

    @model_validator(mode="after")
    def end_not_before_start(self) -> "CycleCreate":
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date can't be before start_date")
        return self


class CyclePatch(BaseModel):
    """Only the fields that are sent change. Send end_date: null to clear it."""

    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None
    notes: Notes | None = None

    @field_validator("start_date")
    @classmethod
    def start_not_null(cls, value: date | None) -> date:
        if value is None:
            raise ValueError("start_date can't be cleared")
        return value


class CycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    start_date: date
    end_date: date | None
    notes: str | None


class CycleStatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date | None
    length_days: int | None
    period_days: int | None
    long_gap: bool


class CycleSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cycles: list[CycleStatOut]
    completed_count: int
    mean_length: float | None
    min_length: int | None
    max_length: int | None
    last_start: date | None
    days_since_last_start: int | None
    gap_threshold: int
    current_gap_over_threshold: bool
