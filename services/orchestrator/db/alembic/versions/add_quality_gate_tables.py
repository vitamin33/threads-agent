"""Add quality gate tables

Revision ID: add_quality_gate
Revises: 991136e1c553
Create Date: 2025-07-23 02:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_quality_gate"
down_revision: Union[str, None] = "991136e1c553"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create quality_gate_events table
    op.create_table(
        "quality_gate_events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=True),
        sa.Column("quality_score", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("persona_id", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quality_gate_events_created_at"),
        "quality_gate_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quality_gate_events_persona_id"),
        "quality_gate_events",
        ["persona_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_quality_gate_events_passed"),
        "quality_gate_events",
        ["passed"],
        unique=False,
    )

    # Create reply_magnetizers table
    op.create_table(
        "reply_magnetizers",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("magnet_type", sa.String(), nullable=False),
        sa.Column("magnet_text", sa.Text(), nullable=False),
        sa.Column("position_in_content", sa.String(), nullable=False),
        sa.Column("reply_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_reply_magnetizers_content_id"),
        "reply_magnetizers",
        ["content_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reply_magnetizers_magnet_type"),
        "reply_magnetizers",
        ["magnet_type"],
        unique=False,
    )

    # Add quality_score column to posts table
    op.add_column(
        "posts",
        sa.Column("quality_score", sa.Numeric(precision=3, scale=2), nullable=True),
    )
    op.create_index(
        op.f("ix_posts_quality_score"), "posts", ["quality_score"], unique=False
    )


def downgrade() -> None:
    # Drop quality_score column from posts
    op.drop_index(op.f("ix_posts_quality_score"), table_name="posts")
    op.drop_column("posts", "quality_score")

    # Drop reply_magnetizers table
    op.drop_index(
        op.f("ix_reply_magnetizers_magnet_type"), table_name="reply_magnetizers"
    )
    op.drop_index(
        op.f("ix_reply_magnetizers_content_id"), table_name="reply_magnetizers"
    )
    op.drop_table("reply_magnetizers")

    # Drop quality_gate_events table
    op.drop_index(
        op.f("ix_quality_gate_events_passed"), table_name="quality_gate_events"
    )
    op.drop_index(
        op.f("ix_quality_gate_events_persona_id"), table_name="quality_gate_events"
    )
    op.drop_index(
        op.f("ix_quality_gate_events_created_at"), table_name="quality_gate_events"
    )
    op.drop_table("quality_gate_events")
