"""add viral metrics tables

Revision ID: 006_add_viral_metrics
Revises: 005_add_revenue_tables
Create Date: 2025-08-01 21:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006_add_viral_metrics"
down_revision = "005_add_revenue_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create viral_metrics table for real-time metrics tracking
    op.create_table(
        "viral_metrics",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("persona_id", sa.String(length=50), nullable=False),
        sa.Column(
            "viral_coefficient", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("scroll_stop_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("share_velocity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reply_depth", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "engagement_trajectory", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "pattern_fatigue_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "collected_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for viral_metrics
    op.create_index("idx_viral_metrics_post_id", "viral_metrics", ["post_id"])
    op.create_index("idx_viral_metrics_collected_at", "viral_metrics", ["collected_at"])
    op.create_index("idx_viral_metrics_persona_id", "viral_metrics", ["persona_id"])

    # Create partial index for recent metrics (performance optimization)
    op.create_index(
        "idx_viral_metrics_recent",
        "viral_metrics",
        ["post_id", "collected_at"],
        postgresql_where=sa.text("collected_at >= NOW() - INTERVAL '7 days'"),
    )

    # Create viral_metrics_history table for time series analysis
    op.create_table(
        "viral_metrics_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for viral_metrics_history
    op.create_index(
        "idx_viral_metrics_history_post_metric",
        "viral_metrics_history",
        ["post_id", "metric_name"],
    )
    op.create_index(
        "idx_viral_metrics_history_recorded_at",
        "viral_metrics_history",
        ["recorded_at"],
    )

    # Create pattern_usage_history table for fatigue tracking
    op.create_table(
        "pattern_usage_history",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("pattern_id", sa.String(length=100), nullable=False),
        sa.Column("persona_id", sa.String(length=50), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "last_used_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for pattern_usage_history
    op.create_index(
        "idx_pattern_usage_pattern_created",
        "pattern_usage_history",
        ["pattern_id", "created_at"],
    )
    op.create_index(
        "idx_pattern_usage_persona_pattern",
        "pattern_usage_history",
        ["persona_id", "pattern_id"],
    )

    # Create viral_metrics_anomalies table for tracking detected anomalies
    op.create_table(
        "viral_metrics_anomalies",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("anomaly_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("metric_name", sa.String(length=50), nullable=False),
        sa.Column("current_value", sa.Float(), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("drop_percentage", sa.Float(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("alert_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "detected_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for viral_metrics_anomalies
    op.create_index(
        "idx_viral_anomalies_post_id", "viral_metrics_anomalies", ["post_id"]
    )
    op.create_index(
        "idx_viral_anomalies_detected_at", "viral_metrics_anomalies", ["detected_at"]
    )
    op.create_index(
        "idx_viral_anomalies_severity", "viral_metrics_anomalies", ["severity"]
    )


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("idx_viral_anomalies_severity", table_name="viral_metrics_anomalies")
    op.drop_index(
        "idx_viral_anomalies_detected_at", table_name="viral_metrics_anomalies"
    )
    op.drop_index("idx_viral_anomalies_post_id", table_name="viral_metrics_anomalies")

    op.drop_index(
        "idx_pattern_usage_persona_pattern", table_name="pattern_usage_history"
    )
    op.drop_index(
        "idx_pattern_usage_pattern_created", table_name="pattern_usage_history"
    )

    op.drop_index(
        "idx_viral_metrics_history_recorded_at", table_name="viral_metrics_history"
    )
    op.drop_index(
        "idx_viral_metrics_history_post_metric", table_name="viral_metrics_history"
    )

    op.drop_index("idx_viral_metrics_recent", table_name="viral_metrics")
    op.drop_index("idx_viral_metrics_persona_id", table_name="viral_metrics")
    op.drop_index("idx_viral_metrics_collected_at", table_name="viral_metrics")
    op.drop_index("idx_viral_metrics_post_id", table_name="viral_metrics")

    # Drop tables
    op.drop_table("viral_metrics_anomalies")
    op.drop_table("pattern_usage_history")
    op.drop_table("viral_metrics_history")
    op.drop_table("viral_metrics")
