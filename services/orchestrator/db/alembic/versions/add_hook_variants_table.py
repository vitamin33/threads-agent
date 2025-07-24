"""add hook variants table

Revision ID: add_hook_variants
Revises:
Create Date: 2025-01-23 14:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_hook_variants"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create hook_variants table for tracking all generated variants
    op.create_table(
        "hook_variants",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("variant_id", sa.Text(), nullable=False),
        sa.Column("batch_id", sa.Text(), nullable=False),
        sa.Column("post_id", sa.BigInteger(), nullable=True),
        sa.Column("pattern_id", sa.Text(), nullable=False),
        sa.Column("pattern_category", sa.Text(), nullable=False),
        sa.Column("emotion_modifier", sa.Text(), nullable=True),
        sa.Column("hook_content", sa.Text(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("original_content", sa.Text(), nullable=False),
        sa.Column("persona_id", sa.Text(), nullable=False),
        sa.Column(
            "expected_engagement_rate", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("actual_engagement_rate", sa.Float(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagements", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "selected_for_posting", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("experiment_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index("idx_variant_id", "hook_variants", ["variant_id"], unique=True)
    op.create_index("idx_batch_id", "hook_variants", ["batch_id"])
    op.create_index("idx_pattern_id", "hook_variants", ["pattern_id"])
    op.create_index("idx_persona_id", "hook_variants", ["persona_id"])
    op.create_index("idx_experiment_id", "hook_variants", ["experiment_id"])
    op.create_index(
        "idx_performance",
        "hook_variants",
        ["actual_engagement_rate"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_performance", table_name="hook_variants")
    op.drop_index("idx_experiment_id", table_name="hook_variants")
    op.drop_index("idx_persona_id", table_name="hook_variants")
    op.drop_index("idx_pattern_id", table_name="hook_variants")
    op.drop_index("idx_batch_id", table_name="hook_variants")
    op.drop_index("idx_variant_id", table_name="hook_variants")

    # Drop table
    op.drop_table("hook_variants")
