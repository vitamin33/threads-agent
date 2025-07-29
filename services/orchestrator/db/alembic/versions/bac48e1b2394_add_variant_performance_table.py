"""add variant performance table

Revision ID: bac48e1b2394
Revises: add_achievement_collector_tables
Create Date: 2025-07-29 18:43:38.273123

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bac48e1b2394'
down_revision: Union[str, Sequence[str], None] = 'add_achievement_collector_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'variant_performance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Text(), nullable=False),
        sa.Column('dimensions', sa.JSON(), nullable=False),
        sa.Column('impressions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variant_performance_variant_id'), 'variant_performance', ['variant_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_variant_performance_variant_id'), table_name='variant_performance')
    op.drop_table('variant_performance')
