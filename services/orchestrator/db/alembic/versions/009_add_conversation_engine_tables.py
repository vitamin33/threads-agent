"""add conversation engine tables

Revision ID: 009_add_conversation_engine
Revises: 008_add_comment_monitoring
Create Date: 2025-08-05 20:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "009_add_conversation_engine"
down_revision = "008_add_comment_monitoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_states table
    op.create_table(
        "conversation_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", sa.String(length=100), nullable=False),
        sa.Column("user_id", sa.String(length=100), nullable=False),
        sa.Column("current_state", sa.String(length=50), nullable=False),
        sa.Column("state_history", sa.JSON(), nullable=True),
        sa.Column("user_profile", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("conversion_probability", sa.Float(), nullable=True),
        sa.Column("last_interaction", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Add indexes for conversation_states
    op.create_index(
        op.f("ix_conversation_states_conversation_id"),
        "conversation_states",
        ["conversation_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_conversation_states_user_id"),
        "conversation_states",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_states_current_state"),
        "conversation_states",
        ["current_state"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_states_last_interaction"),
        "conversation_states",
        ["last_interaction"],
        unique=False,
    )
    
    # Create conversation_turns table
    op.create_table(
        "conversation_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", sa.String(length=100), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("bot_message", sa.Text(), nullable=False),
        sa.Column("state_before", sa.String(length=50), nullable=False),
        sa.Column("state_after", sa.String(length=50), nullable=False),
        sa.Column("intent_analysis", sa.JSON(), nullable=True),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Add indexes for conversation_turns
    op.create_index(
        op.f("ix_conversation_turns_conversation_id"),
        "conversation_turns",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_conversation_turns_turn_number"),
        "conversation_turns",
        ["conversation_id", "turn_number"],
        unique=True,
    )
    op.create_index(
        op.f("ix_conversation_turns_created_at"),
        "conversation_turns",
        ["created_at"],
        unique=False,
    )
    
    # Partial index for active conversations (optimization)
    op.execute("""
        CREATE INDEX ix_conversation_states_active 
        ON conversation_states (user_id, last_interaction) 
        WHERE last_interaction > NOW() - INTERVAL '7 days'
    """)
    
    # Index for analytics queries
    op.execute("""
        CREATE INDEX ix_conversation_states_analytics 
        ON conversation_states (current_state, conversion_probability, created_at)
    """)


def downgrade() -> None:
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS ix_conversation_states_analytics")
    op.execute("DROP INDEX IF EXISTS ix_conversation_states_active")
    
    op.drop_index(op.f("ix_conversation_turns_created_at"), table_name="conversation_turns")
    op.drop_index(op.f("ix_conversation_turns_turn_number"), table_name="conversation_turns")
    op.drop_index(op.f("ix_conversation_turns_conversation_id"), table_name="conversation_turns")
    
    op.drop_index(op.f("ix_conversation_states_last_interaction"), table_name="conversation_states")
    op.drop_index(op.f("ix_conversation_states_current_state"), table_name="conversation_states")
    op.drop_index(op.f("ix_conversation_states_user_id"), table_name="conversation_states")
    op.drop_index(op.f("ix_conversation_states_conversation_id"), table_name="conversation_states")
    
    # Drop tables
    op.drop_table("conversation_turns")
    op.drop_table("conversation_states")