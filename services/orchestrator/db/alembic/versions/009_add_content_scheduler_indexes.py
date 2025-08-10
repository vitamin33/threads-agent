"""Add performance indexes for content scheduler tables

Revision ID: 009_add_content_scheduler_indexes
Revises: 008_add_content_scheduler
Create Date: 2025-08-07

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "009_add_content_scheduler_indexes"
down_revision = "008_add_content_scheduler"
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for content scheduler tables."""

    # Content Items indexes
    # Composite index for author + status queries
    op.create_index(
        "idx_content_items_author_status", "content_items", ["author_id", "status"]
    )

    # Composite index for content type + status queries
    op.create_index(
        "idx_content_items_type_status", "content_items", ["content_type", "status"]
    )

    # Index for slug lookups (unique constraint already provides this)
    # Partial index for draft content (most frequently queried)
    op.execute("""
        CREATE INDEX idx_content_items_draft 
        ON content_items(created_at DESC) 
        WHERE status = 'draft'
    """)

    # Content Schedules indexes
    # Composite index for platform + scheduled time queries
    op.create_index(
        "idx_content_schedules_platform_time",
        "content_schedules",
        ["platform", "scheduled_time"],
    )

    # Composite index for status + scheduled time queries
    op.create_index(
        "idx_content_schedules_status_time",
        "content_schedules",
        ["status", "scheduled_time"],
    )

    # Partial index for upcoming schedules
    op.execute("""
        CREATE INDEX idx_content_schedules_upcoming
        ON content_schedules(scheduled_time)
        WHERE status = 'scheduled' AND scheduled_time > NOW()
    """)

    # Content Analytics indexes
    # Composite index for platform + date range queries
    op.create_index(
        "idx_content_analytics_platform_date",
        "content_analytics",
        ["platform", "published_at"],
    )

    # Index for performance analysis queries
    op.create_index(
        "idx_content_analytics_engagement",
        "content_analytics",
        ["engagement_rate", "published_at"],
    )

    # GIN index for content metadata JSONB queries
    op.execute("""
        CREATE INDEX idx_content_items_metadata_gin
        ON content_items USING gin(content_metadata)
    """)

    # GIN index for schedule platform config JSONB queries
    op.execute("""
        CREATE INDEX idx_content_schedules_config_gin
        ON content_schedules USING gin(platform_config)
    """)


def downgrade():
    """Remove performance indexes."""

    # Drop Content Analytics indexes
    op.drop_index("idx_content_analytics_engagement", "content_analytics")
    op.drop_index("idx_content_analytics_platform_date", "content_analytics")

    # Drop Content Schedules indexes
    op.drop_index("idx_content_schedules_upcoming", "content_schedules")
    op.drop_index("idx_content_schedules_status_time", "content_schedules")
    op.drop_index("idx_content_schedules_platform_time", "content_schedules")

    # Drop Content Items indexes
    op.drop_index("idx_content_items_metadata_gin", "content_items")
    op.drop_index("idx_content_items_draft", "content_items")
    op.drop_index("idx_content_items_type_status", "content_items")
    op.drop_index("idx_content_items_author_status", "content_items")

    # Drop GIN indexes
    op.drop_index("idx_content_schedules_config_gin", "content_schedules")
