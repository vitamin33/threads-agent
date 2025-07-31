"""add pattern usage table

Revision ID: add_pattern_usage_table
Revises: add_variant_performance_indexes
Create Date: 2025-01-31

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_pattern_usage_table"
down_revision = "add_variant_performance_indexes"
branch_labels = None
depends_on = None


def upgrade():
    # Create pattern_usage table
    op.create_table(
        "pattern_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("persona_id", sa.String(50), nullable=False),
        sa.Column("pattern_id", sa.String(100), nullable=False),
        sa.Column("post_id", sa.String(100), nullable=False),
        sa.Column(
            "used_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column("engagement_rate", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for performance
    op.create_index(
        "idx_pattern_usage_persona_pattern",
        "pattern_usage",
        ["persona_id", "pattern_id"],
    )
    op.create_index("idx_pattern_usage_used_at", "pattern_usage", ["used_at"])

    # Create composite index for efficient rolling window queries
    op.create_index(
        "idx_pattern_usage_persona_used_at",
        "pattern_usage",
        ["persona_id", "used_at"],
        postgresql_where=sa.text("used_at >= (CURRENT_TIMESTAMP - INTERVAL '7 days')"),
    )


def downgrade():
    # Drop indexes
    op.drop_index("idx_pattern_usage_persona_used_at", table_name="pattern_usage")
    op.drop_index("idx_pattern_usage_used_at", table_name="pattern_usage")
    op.drop_index("idx_pattern_usage_persona_pattern", table_name="pattern_usage")

    # Drop table
    op.drop_table("pattern_usage")
