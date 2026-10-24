"""create users

Revision ID: 0001
Revises:
Create Date: 2026-10-24
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("auth_sub", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column(
            "conditions",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("track_cycles", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("track_weight", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("ai_consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "conditions <@ ARRAY['pcos', 'thyroid']::text[]", name="users_conditions_known"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_sub"),
    )


def downgrade() -> None:
    op.drop_table("users")
