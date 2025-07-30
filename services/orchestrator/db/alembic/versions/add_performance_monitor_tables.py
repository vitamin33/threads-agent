"""add performance monitor tables

Revision ID: add_performance_monitor_tables
Revises: expand_business_value_column
Create Date: 2025-01-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_performance_monitor_tables'
down_revision = 'expand_business_value_column'
branch_labels = None
depends_on = None


def upgrade():
    # Create variant_monitoring table
    op.create_table('variant_monitoring',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('variant_id', sa.String(), nullable=False),
        sa.Column('persona_id', sa.String(), nullable=False),
        sa.Column('post_id', sa.String(), nullable=True),
        sa.Column('expected_engagement_rate', sa.Float(), nullable=False),
        sa.Column('kill_threshold', sa.Float(), server_default='0.5'),
        sa.Column('min_interactions', sa.Integer(), server_default='10'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('timeout_minutes', sa.Integer(), server_default='10'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('was_killed', sa.Boolean(), server_default='false'),
        sa.Column('kill_reason', sa.String(), nullable=True),
        sa.Column('final_engagement_rate', sa.Float(), nullable=True),
        sa.Column('final_interaction_count', sa.Integer(), nullable=True),
        sa.Column('final_view_count', sa.Integer(), nullable=True),
        sa.Column('monitoring_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_variant_monitoring_variant_id'), 'variant_monitoring', ['variant_id'], unique=False)
    op.create_index(op.f('ix_variant_monitoring_persona_id'), 'variant_monitoring', ['persona_id'], unique=False)
    op.create_index(op.f('ix_variant_monitoring_is_active'), 'variant_monitoring', ['is_active'], unique=False)
    op.create_index(op.f('ix_variant_monitoring_started_at'), 'variant_monitoring', ['started_at'], unique=False)
    
    # Composite index for efficient active variant lookup
    op.create_index('ix_variant_monitoring_variant_active', 'variant_monitoring', ['variant_id', 'is_active'], 
                    unique=False, postgresql_where=sa.text('is_active = TRUE'))


def downgrade():
    # Drop indexes
    op.drop_index('ix_variant_monitoring_variant_active', table_name='variant_monitoring')
    op.drop_index(op.f('ix_variant_monitoring_started_at'), table_name='variant_monitoring')
    op.drop_index(op.f('ix_variant_monitoring_is_active'), table_name='variant_monitoring')
    op.drop_index(op.f('ix_variant_monitoring_persona_id'), table_name='variant_monitoring')
    op.drop_index(op.f('ix_variant_monitoring_variant_id'), table_name='variant_monitoring')
    
    # Drop table
    op.drop_table('variant_monitoring')