"""Expand business_value column from varchar(255) to TEXT for achievement tables

Revision ID: expand_business_value_column
Revises: bac48e1b2394
Create Date: 2025-07-29 17:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "expand_business_value_column"
down_revision = "bac48e1b2394"
branch_labels = None
depends_on = None


def upgrade():
    """Expand business_value column to handle large JSON objects."""
    # Check if achievements table exists and has business_value column
    try:
        # PostgreSQL: Change VARCHAR(255) to TEXT
        op.alter_column(
            "achievements",
            "business_value",
            existing_type=sa.VARCHAR(length=255),
            type_=sa.Text(),
            existing_nullable=True,
        )
    except Exception:
        # Table or column might not exist, skip silently
        pass


def downgrade():
    """Revert business_value column back to VARCHAR(255)."""
    try:
        # WARNING: This may truncate data if JSON is longer than 255 characters
        op.alter_column(
            "achievements",
            "business_value",
            existing_type=sa.Text(),
            type_=sa.VARCHAR(length=255),
            existing_nullable=True,
        )
    except Exception:
        # Table or column might not exist, skip silently
        pass
