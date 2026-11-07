"""food tags, user food tags, meals

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-07
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None

# Copied here (not imported) so this migration never changes if the app's list does.
FOOD_TAGS = [
    ("dairy", "Dairy"),
    ("gluten", "Gluten"),
    ("added_sugar", "Added sugar"),
    ("refined_carbs", "Refined carbs"),
    ("caffeine", "Caffeine"),
    ("alcohol", "Alcohol"),
    ("fried", "Fried"),
    ("high_protein", "High protein"),
    ("high_fiber", "High fiber"),
    ("soy", "Soy"),
    ("spicy", "Spicy"),
    ("processed", "Processed"),
    ("late_night", "Late night"),
]


def upgrade() -> None:
    food_tags = op.create_table(
        "food_tags",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.bulk_insert(food_tags, [{"key": k, "display_name": n} for k, n in FOOD_TAGS])
    op.create_table(
        "user_food_tags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "key", name="user_food_tags_user_key_key"),
    )
    op.create_table(
        "meals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time", sa.Time(), nullable=True),
        sa.Column("meal_type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "meal_type IN ('breakfast', 'lunch', 'dinner', 'snack', 'drink')",
            name="meals_meal_type_known",
        ),
        sa.CheckConstraint("length(description) > 0", name="meals_description_not_empty"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("meals")
    op.drop_table("user_food_tags")
    op.drop_table("food_tags")
