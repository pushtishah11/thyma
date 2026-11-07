"""Database tables.

Every table except users and markers has a user_id foreign key, and every query
filters by it. Pydantic does the real validation; check constraints are a backstop.
"""

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

CONDITIONS = ("pcos", "thyroid")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # Backstop for Pydantic validation: only known conditions are stored.
        CheckConstraint(
            "conditions <@ ARRAY['pcos', 'thyroid']::text[]", name="users_conditions_known"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Set by the auth provider in M7. Null for the local dev user.
    auth_sub: Mapped[str | None] = mapped_column(Text, unique=True)
    email: Mapped[str | None] = mapped_column(Text)
    conditions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'")
    )
    track_cycles: Mapped[bool] = mapped_column(default=True, server_default=text("true"))
    track_weight: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    # Upload extraction and summaries are blocked until this is set (M10).
    ai_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DailyLog(Base):
    """One row per user per day: ratings, sleep, notes, and that day's symptoms."""

    __tablename__ = "daily_logs"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="daily_logs_user_date_key"),
        CheckConstraint("energy BETWEEN 1 AND 5", name="daily_logs_energy_range"),
        CheckConstraint("mood BETWEEN 1 AND 5", name="daily_logs_mood_range"),
        CheckConstraint("sleep_hours BETWEEN 0 AND 24", name="daily_logs_sleep_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    energy: Mapped[int | None] = mapped_column(SmallInteger)
    mood: Mapped[int | None] = mapped_column(SmallInteger)
    sleep_hours: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    # Only accepted when the user has turned on track_weight (checked in the API).
    weight: Mapped[Decimal | None] = mapped_column(Numeric)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    symptoms: Mapped[list["LogSymptom"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LogSymptom.symptom",
    )


class LogSymptom(Base):
    """A symptom logged on one day, with severity 1 (mild) to 3 (severe)."""

    __tablename__ = "log_symptoms"
    __table_args__ = (
        UniqueConstraint("log_id", "symptom", name="log_symptoms_log_symptom_key"),
        CheckConstraint("severity BETWEEN 1 AND 3", name="log_symptoms_severity_range"),
        CheckConstraint("symptom = lower(symptom)", name="log_symptoms_symptom_lowercase"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    log_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("daily_logs.id", ondelete="CASCADE"))
    symptom: Mapped[str] = mapped_column(Text)
    severity: Mapped[int] = mapped_column(SmallInteger)

    log: Mapped[DailyLog] = relationship(back_populates="symptoms")


class TrackedSymptom(Base):
    """The user's symptom chip list on the Today page, in display order."""

    __tablename__ = "tracked_symptoms"
    __table_args__ = (
        UniqueConstraint("user_id", "symptom", name="tracked_symptoms_user_symptom_key"),
        CheckConstraint("symptom = lower(symptom)", name="tracked_symptoms_symptom_lowercase"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symptom: Mapped[str] = mapped_column(Text)
    position: Mapped[int]
    # Hiding a chip keeps its history; deleting is only for typos.
    active: Mapped[bool] = mapped_column(default=True, server_default=text("true"))


class Cycle(Base):
    """One period: the day bleeding started, and optionally the last bleeding day.

    Cycle length is measured start to next start, so it's computed, not stored.
    There is no "expected" length and no prediction anywhere.
    """

    __tablename__ = "cycles"
    __table_args__ = (
        UniqueConstraint("user_id", "start_date", name="cycles_user_start_key"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="cycles_end_after_start"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Medication(Base):
    """A medication or supplement, at one dose, over a span of dates.

    A dose change ends this row and starts a new one, so the history stays honest:
    each row is exactly what was taken, and when.
    """

    __tablename__ = "medications"
    __table_args__ = (
        CheckConstraint("kind IN ('medication', 'supplement')", name="medications_kind_known"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date", name="medications_end_after_start"
        ),
        CheckConstraint("dose IS NULL OR dose > 0", name="medications_dose_positive"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    dose: Mapped[Decimal | None] = mapped_column(Numeric)
    dose_unit: Mapped[str | None] = mapped_column(Text)
    frequency: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MedDose(Base):
    """Whether a medication or supplement was taken on one day."""

    __tablename__ = "med_doses"
    __table_args__ = (UniqueConstraint("medication_id", "date", name="med_doses_med_date_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    medication_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE")
    )
    date: Mapped[date] = mapped_column(Date)
    taken: Mapped[bool]
    time_taken: Mapped[time | None] = mapped_column(Time)
    notes: Mapped[str | None] = mapped_column(Text)
