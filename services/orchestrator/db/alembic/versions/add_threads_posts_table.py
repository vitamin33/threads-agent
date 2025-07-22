"""add threads posts table

Revision ID: threads_posts_001
Revises: add_quality_gate_tables
Create Date: 2025-07-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'threads_posts_001'
down_revision = 'add_quality_gate_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create threads_posts table
    op.create_table('threads_posts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=True),
        sa.Column('persona_id', sa.String(), nullable=True),
        sa.Column('content', sa.String(), nullable=True),
        sa.Column('media_type', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('engagement_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('likes_count', sa.Integer(), nullable=True),
        sa.Column('comments_count', sa.Integer(), nullable=True),
        sa.Column('shares_count', sa.Integer(), nullable=True),
        sa.Column('impressions_count', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_threads_posts_persona_id'), 'threads_posts', ['persona_id'], unique=False)
    op.create_index(op.f('ix_threads_posts_thread_id'), 'threads_posts', ['thread_id'], unique=True)


def downgrade() -> None:
    # Drop threads_posts table
    op.drop_index(op.f('ix_threads_posts_thread_id'), table_name='threads_posts')
    op.drop_index(op.f('ix_threads_posts_persona_id'), table_name='threads_posts')
    op.drop_table('threads_posts')