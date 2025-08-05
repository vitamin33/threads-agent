"""add comment monitoring tables

Revision ID: 008_add_comment_monitoring
Revises: 007_add_emotion_trajectory
Create Date: 2025-01-25 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008_add_comment_monitoring"
down_revision = "007_add_emotion_trajectory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create comments table for storing raw comments from posts
    op.create_table(
        "comments",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("comment_id", sa.String(length=100), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=100), nullable=False),
        sa.Column("timestamp", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add optimized indexes for efficient querying
    op.create_index(
        op.f("ix_comments_comment_id"), "comments", ["comment_id"], unique=True
    )
    op.create_index(op.f("ix_comments_post_id"), "comments", ["post_id"], unique=False)
    
    # Composite index for time-range queries by post (performance optimization)
    op.create_index(
        "ix_comments_post_timestamp", "comments", ["post_id", "created_at"], unique=False
    )
    
    # Index for author analysis queries
    op.create_index(
        "ix_comments_author_timestamp", "comments", ["author", "created_at"], unique=False
    )
    
    # Partial index for recent comments (hot data optimization)
    op.execute("""
        CREATE INDEX ix_comments_recent ON comments (post_id, created_at) 
        WHERE created_at > NOW() - INTERVAL '7 days'
    """)


def downgrade() -> None:
    # Drop indexes first (including new optimized indexes)
    op.execute("DROP INDEX IF EXISTS ix_comments_recent")
    op.drop_index("ix_comments_author_timestamp", table_name="comments")
    op.drop_index("ix_comments_post_timestamp", table_name="comments")
    op.drop_index(op.f("ix_comments_post_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_comment_id"), table_name="comments")

    # Drop table
    op.drop_table("comments")