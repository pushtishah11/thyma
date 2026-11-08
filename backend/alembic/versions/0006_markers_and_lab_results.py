"""markers catalog and lab results

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-08
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None

# The v1 catalog: (key, display name, category, aliases). Aliases are lowercase names
# commonly printed on lab reports; M4 matches extracted rows against them. Kept in this
# file (not imported) so the migration never changes if the app's code does.
MARKERS = [
    # Thyroid
    (
        "tsh",
        "TSH",
        "thyroid",
        [
            "tsh",
            "thyroid stimulating hormone",
            "thyrotropin",
            "tsh 3rd gen",
            "tsh, 3rd generation",
            "tsh ultrasensitive",
        ],
    ),
    (
        "free_t4",
        "Free T4",
        "thyroid",
        ["free t4", "ft4", "t4, free", "free thyroxine", "thyroxine, free", "t4 free (direct)"],
    ),
    (
        "free_t3",
        "Free T3",
        "thyroid",
        ["free t3", "ft3", "t3, free", "free triiodothyronine", "triiodothyronine, free"],
    ),
    (
        "total_t3",
        "Total T3",
        "thyroid",
        ["total t3", "t3", "t3, total", "triiodothyronine", "triiodothyronine, total"],
    ),
    (
        "tpo_antibodies",
        "TPO antibodies",
        "thyroid",
        [
            "tpo antibodies",
            "tpo ab",
            "anti-tpo",
            "thyroid peroxidase antibodies",
            "thyroid peroxidase ab",
            "antithyroid peroxidase",
        ],
    ),
    (
        "thyroglobulin_antibodies",
        "Thyroglobulin antibodies",
        "thyroid",
        [
            "thyroglobulin antibodies",
            "tg ab",
            "tgab",
            "anti-tg",
            "anti-thyroglobulin",
            "thyroglobulin ab",
        ],
    ),
    # Androgens
    (
        "total_testosterone",
        "Total testosterone",
        "androgens",
        ["total testosterone", "testosterone", "testosterone, total", "testosterone total"],
    ),
    (
        "free_testosterone",
        "Free testosterone",
        "androgens",
        ["free testosterone", "testosterone, free", "testosterone free"],
    ),
    (
        "dhea_s",
        "DHEA-S",
        "androgens",
        [
            "dhea-s",
            "dheas",
            "dhea sulfate",
            "dhea-sulfate",
            "dehydroepiandrosterone sulfate",
            "dhea-so4",
        ],
    ),
    (
        "shbg",
        "SHBG",
        "androgens",
        ["shbg", "sex hormone binding globulin", "sex hormone-binding globulin"],
    ),
    (
        "androstenedione",
        "Androstenedione",
        "androgens",
        ["androstenedione", "a4", "delta-4-androstenedione"],
    ),
    # Reproductive
    ("lh", "LH", "reproductive", ["lh", "luteinizing hormone", "luteinising hormone"]),
    (
        "fsh",
        "FSH",
        "reproductive",
        ["fsh", "follicle stimulating hormone", "follicle-stimulating hormone"],
    ),
    (
        "amh",
        "AMH",
        "reproductive",
        [
            "amh",
            "anti-mullerian hormone",
            "anti-müllerian hormone",
            "mullerian inhibiting substance",
        ],
    ),
    ("estradiol", "Estradiol", "reproductive", ["estradiol", "oestradiol", "e2", "estradiol (e2)"]),
    ("progesterone", "Progesterone", "reproductive", ["progesterone", "p4"]),
    ("prolactin", "Prolactin", "reproductive", ["prolactin", "prl"]),
    # Metabolic
    (
        "fasting_glucose",
        "Fasting glucose",
        "metabolic",
        [
            "fasting glucose",
            "glucose, fasting",
            "glucose fasting",
            "fasting blood sugar",
            "fbs",
            "fasting plasma glucose",
            "glucose",
        ],
    ),
    (
        "fasting_insulin",
        "Fasting insulin",
        "metabolic",
        ["fasting insulin", "insulin, fasting", "insulin fasting", "insulin"],
    ),
    (
        "hba1c",
        "HbA1c",
        "metabolic",
        [
            "hba1c",
            "hemoglobin a1c",
            "haemoglobin a1c",
            "a1c",
            "glycated hemoglobin",
            "glycosylated hemoglobin",
        ],
    ),
    (
        "total_cholesterol",
        "Total cholesterol",
        "metabolic",
        ["total cholesterol", "cholesterol, total", "cholesterol"],
    ),
    (
        "ldl",
        "LDL cholesterol",
        "metabolic",
        ["ldl", "ldl cholesterol", "ldl-c", "ldl cholesterol calc", "low density lipoprotein"],
    ),
    (
        "hdl",
        "HDL cholesterol",
        "metabolic",
        ["hdl", "hdl cholesterol", "hdl-c", "high density lipoprotein"],
    ),
    ("triglycerides", "Triglycerides", "metabolic", ["triglycerides", "triglyceride", "tg"]),
    # Other
    (
        "vitamin_d",
        "Vitamin D",
        "other",
        [
            "vitamin d",
            "25-oh vitamin d",
            "vitamin d, 25-hydroxy",
            "25-hydroxyvitamin d",
            "vit d",
            "25(oh)d",
        ],
    ),
    ("ferritin", "Ferritin", "other", ["ferritin", "serum ferritin"]),
    (
        "b12",
        "Vitamin B12",
        "other",
        ["vitamin b12", "b12", "cobalamin", "vit b12", "cyanocobalamin"],
    ),
]


def upgrade() -> None:
    markers = op.create_table(
        "markers",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=False),
        sa.Column("aliases", sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "category IN ('thyroid', 'androgens', 'reproductive', 'metabolic', 'other')",
            name="markers_category_known",
        ),
        sa.PrimaryKeyConstraint("key"),
    )
    op.bulk_insert(
        markers,
        [
            {"key": k, "display_name": n, "category": c, "aliases": a, "position": i}
            for i, (k, n, c, a) in enumerate(MARKERS)
        ],
    )
    op.create_table(
        "lab_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("marker_key", sa.Text(), nullable=True),
        sa.Column("raw_marker", sa.Text(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("ref_low", sa.Numeric(), nullable=True),
        sa.Column("ref_high", sa.Numeric(), nullable=True),
        sa.Column("ref_text", sa.Text(), nullable=True),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("source_line", sa.Text(), nullable=True),
        sa.Column("confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "ref_low IS NULL OR ref_high IS NULL OR ref_low <= ref_high",
            name="lab_results_ref_range_ordered",
        ),
        sa.ForeignKeyConstraint(["marker_key"], ["markers.key"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("lab_results")
    op.drop_table("markers")
