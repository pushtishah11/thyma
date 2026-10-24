"""Database tables.

Every table except users and markers gets a user_id foreign key (added in M1+).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

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
