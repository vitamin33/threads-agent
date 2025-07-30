"""Add performance indexes for variant_performance table

Revision ID: add_variant_performance_indexes
Revises:
Create Date: 2025-01-29

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_variant_performance_indexes"
down_revision = "add_performance_monitor_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes for Thompson Sampling optimization."""

    # Add composite index for filtering active variants
    op.create_index(
        "idx_variant_performance_active",
        "variant_performance",
        ["impressions", "created_at"],
        postgresql_where=sa.text("impressions > 0"),
    )

    # Add index for sorting by last_used
    op.create_index(
        "idx_variant_performance_last_used",
        "variant_performance",
        [sa.text("last_used DESC")],
    )

    # Add index for persona filtering (JSON field)
    op.execute("""
        CREATE INDEX idx_variant_performance_persona 
        ON variant_performance ((dimensions->>'persona_id'))
        WHERE dimensions->>'persona_id' IS NOT NULL
    """)

    # Add partial index for high-performing variants
    op.create_index(
        "idx_variant_performance_high_performers",
        "variant_performance",
        ["variant_id", "impressions", "successes"],
        postgresql_where=sa.text("impressions >= 100"),
    )

    # Add index for batch updates
    op.create_index(
        "idx_variant_performance_batch_update",
        "variant_performance",
        ["variant_id"],
        postgresql_where=sa.text("impressions > 0 OR successes > 0"),
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index(
        "idx_variant_performance_batch_update", table_name="variant_performance"
    )
    op.drop_index(
        "idx_variant_performance_high_performers", table_name="variant_performance"
    )
    op.drop_index("idx_variant_performance_persona", table_name="variant_performance")
    op.drop_index("idx_variant_performance_last_used", table_name="variant_performance")
    op.drop_index("idx_variant_performance_active", table_name="variant_performance")
