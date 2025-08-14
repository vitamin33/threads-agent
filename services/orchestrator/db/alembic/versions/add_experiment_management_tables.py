"""add experiment management tables

Revision ID: add_experiment_management_tables
Revises: add_variant_performance_indexes
Create Date: 2025-08-14 01:58:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_experiment_management_tables"
down_revision = "add_variant_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add experiment management tables for A/B testing."""

    # Create experiments table
    op.create_table(
        "experiments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        # Experiment configuration
        sa.Column("variant_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("traffic_allocation", postgresql.ARRAY(sa.Float()), nullable=True),
        sa.Column("control_variant_id", sa.Text(), nullable=True),
        sa.Column("target_persona", sa.Text(), nullable=False),
        sa.Column("success_metrics", postgresql.ARRAY(sa.String()), nullable=True),
        # Experiment lifecycle
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("expected_end_time", sa.DateTime(), nullable=True),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        # Statistical parameters
        sa.Column("min_sample_size", sa.Integer(), nullable=True),
        sa.Column("significance_level", sa.Float(), nullable=True),
        sa.Column("minimum_detectable_effect", sa.Float(), nullable=True),
        # Results tracking
        sa.Column("total_participants", sa.Integer(), nullable=True),
        sa.Column("winner_variant_id", sa.Text(), nullable=True),
        sa.Column("improvement_percentage", sa.Float(), nullable=True),
        sa.Column("is_statistically_significant", sa.Boolean(), nullable=True),
        sa.Column("p_value", sa.Float(), nullable=True),
        # Metadata
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id"),
    )

    # Create indexes for experiments table
    op.create_index("idx_experiments_experiment_id", "experiments", ["experiment_id"])
    op.create_index("idx_experiments_target_persona", "experiments", ["target_persona"])
    op.create_index("idx_experiments_status", "experiments", ["status"])
    op.create_index("idx_experiments_start_time", "experiments", ["start_time"])
    op.create_index("idx_experiments_end_time", "experiments", ["end_time"])

    # Create experiment_events table
    op.create_table(
        "experiment_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=True),
        # Event details
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("participant_id", sa.Text(), nullable=True),
        sa.Column("variant_id", sa.Text(), nullable=False),
        # Engagement data
        sa.Column("action_taken", sa.Text(), nullable=True),
        sa.Column("engagement_value", sa.Float(), nullable=True),
        # Context
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.experiment_id"]),
    )

    # Create indexes for experiment_events table
    op.create_index(
        "idx_experiment_events_experiment_id", "experiment_events", ["experiment_id"]
    )
    op.create_index(
        "idx_experiment_events_event_type", "experiment_events", ["event_type"]
    )
    op.create_index(
        "idx_experiment_events_participant_id", "experiment_events", ["participant_id"]
    )
    op.create_index(
        "idx_experiment_events_variant_id", "experiment_events", ["variant_id"]
    )
    op.create_index(
        "idx_experiment_events_timestamp", "experiment_events", ["timestamp"]
    )

    # Create experiment_variants table
    op.create_table(
        "experiment_variants",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=True),
        sa.Column("variant_id", sa.Text(), nullable=True),
        # Traffic allocation
        sa.Column("allocated_traffic", sa.Float(), nullable=False),
        sa.Column("actual_traffic", sa.Float(), nullable=True),
        # Performance within this experiment
        sa.Column("participants", sa.Integer(), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=True),
        sa.Column("conversions", sa.Integer(), nullable=True),
        sa.Column("conversion_rate", sa.Float(), nullable=True),
        # Statistical data
        sa.Column("confidence_lower", sa.Float(), nullable=True),
        sa.Column("confidence_upper", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.experiment_id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["variant_performance.variant_id"]),
    )

    # Create indexes for experiment_variants table
    op.create_index(
        "idx_experiment_variants_experiment_id",
        "experiment_variants",
        ["experiment_id"],
    )
    op.create_index(
        "idx_experiment_variants_variant_id", "experiment_variants", ["variant_id"]
    )

    # Create experiment_segments table
    op.create_table(
        "experiment_segments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.Text(), nullable=True),
        # Segment definition
        sa.Column("segment_name", sa.Text(), nullable=False),
        sa.Column("segment_filter", sa.JSON(), nullable=False),
        # Segment performance
        sa.Column("total_participants", sa.Integer(), nullable=True),
        sa.Column("variant_performance", sa.JSON(), nullable=True),
        # Statistical significance for this segment
        sa.Column("is_significant", sa.Boolean(), nullable=True),
        sa.Column("p_value", sa.Float(), nullable=True),
        sa.Column("confidence_level", sa.Float(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.experiment_id"]),
    )

    # Create indexes for experiment_segments table
    op.create_index(
        "idx_experiment_segments_experiment_id",
        "experiment_segments",
        ["experiment_id"],
    )
    op.create_index(
        "idx_experiment_segments_segment_name", "experiment_segments", ["segment_name"]
    )


def downgrade() -> None:
    """Remove experiment management tables."""

    # Drop indexes first
    op.drop_index(
        "idx_experiment_segments_segment_name", table_name="experiment_segments"
    )
    op.drop_index(
        "idx_experiment_segments_experiment_id", table_name="experiment_segments"
    )
    op.drop_index(
        "idx_experiment_variants_variant_id", table_name="experiment_variants"
    )
    op.drop_index(
        "idx_experiment_variants_experiment_id", table_name="experiment_variants"
    )
    op.drop_index("idx_experiment_events_timestamp", table_name="experiment_events")
    op.drop_index("idx_experiment_events_variant_id", table_name="experiment_events")
    op.drop_index(
        "idx_experiment_events_participant_id", table_name="experiment_events"
    )
    op.drop_index("idx_experiment_events_event_type", table_name="experiment_events")
    op.drop_index("idx_experiment_events_experiment_id", table_name="experiment_events")
    op.drop_index("idx_experiments_end_time", table_name="experiments")
    op.drop_index("idx_experiments_start_time", table_name="experiments")
    op.drop_index("idx_experiments_status", table_name="experiments")
    op.drop_index("idx_experiments_target_persona", table_name="experiments")
    op.drop_index("idx_experiments_experiment_id", table_name="experiments")

    # Drop tables in reverse order of dependencies
    op.drop_table("experiment_segments")
    op.drop_table("experiment_variants")
    op.drop_table("experiment_events")
    op.drop_table("experiments")
