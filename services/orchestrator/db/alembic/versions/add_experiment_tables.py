"""add experiment tables

Revision ID: add_experiment_tables
Revises: add_hook_variants
Create Date: 2025-01-23 15:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_experiment_tables"
down_revision: Union[str, None] = "add_hook_variants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create experiments table
    op.create_table(
        "experiments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("persona_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("type", sa.Text(), nullable=False, server_default="ab_test"),
        # Configuration
        sa.Column(
            "min_sample_size", sa.Integer(), nullable=False, server_default="100"
        ),
        sa.Column(
            "max_duration_hours", sa.Integer(), nullable=False, server_default="72"
        ),
        sa.Column(
            "confidence_level", sa.Float(), nullable=False, server_default="0.95"
        ),
        sa.Column("power", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("posts_per_hour", sa.Integer(), nullable=False, server_default="2"),
        sa.Column(
            "posting_hours",
            sa.Text(),
            nullable=False,
            server_default='{"start": 9, "end": 21}',
        ),
        # Results
        sa.Column("winner_variant_id", sa.Text(), nullable=True),
        sa.Column(
            "significance_achieved",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("p_value", sa.Float(), nullable=True),
        sa.Column("stopping_reason", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create experiment_variants table
    op.create_table(
        "experiment_variants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=False),
        sa.Column("variant_id", sa.Text(), nullable=False),
        # Assignment
        sa.Column(
            "traffic_allocation", sa.Float(), nullable=False, server_default="0.5"
        ),
        sa.Column("is_control", sa.Boolean(), nullable=False, server_default="false"),
        # Performance
        sa.Column("posts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "impressions_total", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "engagements_total", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("engagement_rate", sa.Float(), nullable=True),
        # Statistical data
        sa.Column("conversion_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mean_engagement", sa.Float(), nullable=True),
        sa.Column("variance", sa.Float(), nullable=True),
        sa.Column("standard_error", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index("idx_experiment_id", "experiments", ["experiment_id"], unique=True)
    op.create_index("idx_experiment_status", "experiments", ["status"])
    op.create_index("idx_experiment_persona", "experiments", ["persona_id"])

    op.create_index(
        "idx_exp_variant_experiment", "experiment_variants", ["experiment_id"]
    )
    op.create_index("idx_exp_variant_variant", "experiment_variants", ["variant_id"])
    op.create_index("idx_exp_variant_control", "experiment_variants", ["is_control"])
    op.create_index(
        "idx_exp_variant_performance", "experiment_variants", ["engagement_rate"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_exp_variant_performance", table_name="experiment_variants")
    op.drop_index("idx_exp_variant_control", table_name="experiment_variants")
    op.drop_index("idx_exp_variant_variant", table_name="experiment_variants")
    op.drop_index("idx_exp_variant_experiment", table_name="experiment_variants")

    op.drop_index("idx_experiment_persona", table_name="experiments")
    op.drop_index("idx_experiment_status", table_name="experiments")
    op.drop_index("idx_experiment_id", table_name="experiments")

    # Drop tables
    op.drop_table("experiment_variants")
    op.drop_table("experiments")
