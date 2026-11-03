"""daily logs, log symptoms, tracked symptoms

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-03
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "daily_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("energy", sa.SmallInteger(), nullable=True),
        sa.Column("mood", sa.SmallInteger(), nullable=True),
        sa.Column("sleep_hours", sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column("weight", sa.Numeric(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("energy BETWEEN 1 AND 5", name="daily_logs_energy_range"),
        sa.CheckConstraint("mood BETWEEN 1 AND 5", name="daily_logs_mood_range"),
        sa.CheckConstraint("sleep_hours BETWEEN 0 AND 24", name="daily_logs_sleep_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="daily_logs_user_date_key"),
    )
    op.create_table(
        "tracked_symptoms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("symptom = lower(symptom)", name="tracked_symptoms_symptom_lowercase"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "symptom", name="tracked_symptoms_user_symptom_key"),
    )
    op.create_table(
        "log_symptoms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("log_id", sa.Uuid(), nullable=False),
        sa.Column("symptom", sa.Text(), nullable=False),
        sa.Column("severity", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("severity BETWEEN 1 AND 3", name="log_symptoms_severity_range"),
        sa.CheckConstraint("symptom = lower(symptom)", name="log_symptoms_symptom_lowercase"),
        sa.ForeignKeyConstraint(["log_id"], ["daily_logs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("log_id", "symptom", name="log_symptoms_log_symptom_key"),
    )


def downgrade() -> None:
    op.drop_table("log_symptoms")
    op.drop_table("tracked_symptoms")
    op.drop_table("daily_logs")
