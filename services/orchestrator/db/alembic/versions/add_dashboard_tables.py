"""Add dashboard-related tables for variant monitoring

Revision ID: add_dashboard_tables
Revises: add_pattern_usage_table
Create Date: 2025-01-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_dashboard_tables'
down_revision = 'add_pattern_usage_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Skip creating variant_monitoring table as it's already created in add_performance_monitor_tables.py
    # The add_performance_monitor_tables migration creates this table with a different schema
    # We'll just ensure any missing columns are added if needed in future migrations
    
    # Create variant_kills table for tracking early kills
    op.create_table('variant_kills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.Text(), nullable=False),
        sa.Column('persona_id', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('final_engagement_rate', sa.Float(), nullable=True),
        sa.Column('sample_size', sa.Integer(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=False),
        sa.Column('killed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for kill statistics
    op.create_index('idx_variant_kills_persona', 'variant_kills', ['persona_id'])
    op.create_index('idx_variant_kills_date', 'variant_kills', ['killed_at'])
    op.create_index('idx_variant_kills_reason', 'variant_kills', ['reason'])
    
    # Create variants table if it doesn't exist
    op.create_table('variants',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('persona_id', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('predicted_er', sa.Float(), nullable=False),
        sa.Column('pattern_used', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), default='active'),
        sa.Column('posted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for variants
    op.create_index('idx_variants_persona', 'variants', ['persona_id'])
    op.create_index('idx_variants_status', 'variants', ['status'])
    op.create_index('idx_variants_posted', 'variants', ['posted_at'])
    
    # Create dashboard_events table for audit trail
    op.create_table('dashboard_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('persona_id', sa.Text(), nullable=False),
        sa.Column('variant_id', sa.Text(), nullable=True),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_dashboard_events_type', 'dashboard_events', ['event_type'])
    op.create_index('idx_dashboard_events_persona', 'dashboard_events', ['persona_id'])
    op.create_index('idx_dashboard_events_created', 'dashboard_events', ['created_at'])


def downgrade() -> None:
    op.drop_table('dashboard_events')
    op.drop_table('variants')
    op.drop_table('variant_kills')
    # Don't drop variant_monitoring as it's managed by add_performance_monitor_tables.py