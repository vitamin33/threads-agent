"""Expand business_value column from varchar(255) to TEXT

Revision ID: 002_expand_business_value_column
Revises: 001_add_pr_achievement_tables
Create Date: 2025-07-29 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_expand_business_value_column'
down_revision = '001_add_pr_achievement_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Expand business_value column to handle large JSON objects."""
    # PostgreSQL: Change VARCHAR(255) to TEXT
    op.alter_column('achievements', 'business_value',
                   existing_type=sa.VARCHAR(length=255),
                   type_=sa.Text(),
                   existing_nullable=True)


def downgrade():
    """Revert business_value column back to VARCHAR(255)."""
    # WARNING: This may truncate data if JSON is longer than 255 characters
    op.alter_column('achievements', 'business_value',
                   existing_type=sa.Text(),
                   type_=sa.VARCHAR(length=255),
                   existing_nullable=True)