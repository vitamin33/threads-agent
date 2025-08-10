"""add content scheduler tables

Revision ID: 008_add_content_scheduler
Revises: 007_add_emotion_trajectory
Create Date: 2025-08-05 16:30:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008_add_content_scheduler"
down_revision = "007_add_emotion_trajectory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_items table for primary content storage
    op.create_table(
        "content_items",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("author_id", sa.String(length=100), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="draft"
        ),
        sa.Column("slug", sa.String(length=200), nullable=True),
        sa.Column("content_metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_content_items_slug"),
    )

    # Create indexes for content_items
    op.create_index("idx_content_items_title", "content_items", ["title"])
    op.create_index("idx_content_items_content_type", "content_items", ["content_type"])
    op.create_index("idx_content_items_author_id", "content_items", ["author_id"])
    op.create_index("idx_content_items_status", "content_items", ["status"])
    op.create_index("idx_content_items_slug", "content_items", ["slug"])
    op.create_index("idx_content_items_created_at", "content_items", ["created_at"])

    # Composite indexes for common queries
    op.create_index(
        "idx_content_items_author_status",
        "content_items",
        ["author_id", "status"],
    )
    op.create_index(
        "idx_content_items_type_status",
        "content_items",
        ["content_type", "status"],
    )

    # Create content_schedules table for multi-platform scheduling
    op.create_table(
        "content_schedules",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("content_item_id", sa.BigInteger(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("scheduled_time", sa.DateTime(), nullable=False),
        sa.Column(
            "timezone_name", sa.String(length=50), nullable=False, server_default="UTC"
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="scheduled"
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("next_retry_time", sa.DateTime(), nullable=True),
        sa.Column("platform_config", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["content_item_id"], ["content_items.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for content_schedules
    op.create_index(
        "idx_content_schedules_content_item_id",
        "content_schedules",
        ["content_item_id"],
    )
    op.create_index("idx_content_schedules_platform", "content_schedules", ["platform"])
    op.create_index(
        "idx_content_schedules_scheduled_time", "content_schedules", ["scheduled_time"]
    )
    op.create_index("idx_content_schedules_status", "content_schedules", ["status"])

    # Composite indexes for scheduling queries
    op.create_index(
        "idx_content_schedules_platform_status",
        "content_schedules",
        ["platform", "status"],
    )
    op.create_index(
        "idx_content_schedules_status_scheduled_time",
        "content_schedules",
        ["status", "scheduled_time"],
    )
    op.create_index(
        "idx_content_schedules_content_platform",
        "content_schedules",
        ["content_item_id", "platform"],
    )

    # Create content_analytics table for performance tracking
    op.create_table(
        "content_analytics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("content_item_id", sa.BigInteger(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("additional_metrics", sa.JSON(), nullable=True),
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["content_item_id"], ["content_items.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for content_analytics
    op.create_index(
        "idx_content_analytics_content_item_id",
        "content_analytics",
        ["content_item_id"],
    )
    op.create_index("idx_content_analytics_platform", "content_analytics", ["platform"])
    op.create_index(
        "idx_content_analytics_engagement_rate",
        "content_analytics",
        ["engagement_rate"],
    )
    op.create_index(
        "idx_content_analytics_measured_at", "content_analytics", ["measured_at"]
    )

    # Composite indexes for analytics queries
    op.create_index(
        "idx_content_analytics_content_platform",
        "content_analytics",
        ["content_item_id", "platform"],
    )
    op.create_index(
        "idx_content_analytics_platform_measured",
        "content_analytics",
        ["platform", "measured_at"],
    )
    op.create_index(
        "idx_content_analytics_engagement_measured",
        "content_analytics",
        ["engagement_rate", "measured_at"],
    )


def downgrade() -> None:
    # Drop indexes first, then tables (reverse order of creation)

    # content_analytics indexes
    op.drop_index(
        "idx_content_analytics_engagement_measured", table_name="content_analytics"
    )
    op.drop_index(
        "idx_content_analytics_platform_measured", table_name="content_analytics"
    )
    op.drop_index(
        "idx_content_analytics_content_platform", table_name="content_analytics"
    )
    op.drop_index("idx_content_analytics_measured_at", table_name="content_analytics")
    op.drop_index(
        "idx_content_analytics_engagement_rate", table_name="content_analytics"
    )
    op.drop_index("idx_content_analytics_platform", table_name="content_analytics")
    op.drop_index(
        "idx_content_analytics_content_item_id", table_name="content_analytics"
    )

    # content_schedules indexes
    op.drop_index(
        "idx_content_schedules_content_platform", table_name="content_schedules"
    )
    op.drop_index(
        "idx_content_schedules_status_scheduled_time", table_name="content_schedules"
    )
    op.drop_index(
        "idx_content_schedules_platform_status", table_name="content_schedules"
    )
    op.drop_index("idx_content_schedules_status", table_name="content_schedules")
    op.drop_index(
        "idx_content_schedules_scheduled_time", table_name="content_schedules"
    )
    op.drop_index("idx_content_schedules_platform", table_name="content_schedules")
    op.drop_index(
        "idx_content_schedules_content_item_id", table_name="content_schedules"
    )

    # content_items indexes
    op.drop_index("idx_content_items_type_status", table_name="content_items")
    op.drop_index("idx_content_items_author_status", table_name="content_items")
    op.drop_index("idx_content_items_created_at", table_name="content_items")
    op.drop_index("idx_content_items_slug", table_name="content_items")
    op.drop_index("idx_content_items_status", table_name="content_items")
    op.drop_index("idx_content_items_author_id", table_name="content_items")
    op.drop_index("idx_content_items_content_type", table_name="content_items")
    op.drop_index("idx_content_items_title", table_name="content_items")

    # Drop tables (reverse order due to foreign key constraints)
    op.drop_table("content_analytics")
    op.drop_table("content_schedules")
    op.drop_table("content_items")
