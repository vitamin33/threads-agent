"""add emotion trajectory tables

Revision ID: 007_add_emotion_trajectory
Revises: 006_add_viral_metrics
Create Date: 2025-08-03 18:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "007_add_emotion_trajectory"
down_revision = "006_add_viral_metrics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create emotion_trajectories table for storing emotion analysis results
    op.create_table(
        "emotion_trajectories",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("persona_id", sa.String(length=50), nullable=False),
        sa.Column(
            "content_hash", sa.String(length=64), nullable=False
        ),  # SHA256 hash for deduplication
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column("total_duration_words", sa.Integer(), nullable=False),
        sa.Column(
            "analysis_model",
            sa.String(length=50),
            nullable=False,
            server_default="bert_vader",
        ),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        # Trajectory characteristics
        sa.Column(
            "trajectory_type", sa.String(length=20), nullable=False
        ),  # rising, falling, roller-coaster, steady
        sa.Column(
            "emotional_variance", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column("peak_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valley_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("transition_count", sa.Integer(), nullable=False, server_default="0"),
        # Primary emotions (BERT model outputs: 8 emotions)
        sa.Column("joy_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("anger_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fear_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sadness_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("surprise_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("disgust_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trust_avg", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("anticipation_avg", sa.Float(), nullable=False, server_default="0.0"),
        # Sentiment analysis (VADER outputs)
        sa.Column(
            "sentiment_compound", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_positive", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_neutral", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_negative", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Performance metrics
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for emotion_trajectories
    op.create_index(
        "idx_emotion_trajectories_post_id", "emotion_trajectories", ["post_id"]
    )
    op.create_index(
        "idx_emotion_trajectories_persona_id", "emotion_trajectories", ["persona_id"]
    )
    op.create_index(
        "idx_emotion_trajectories_content_hash",
        "emotion_trajectories",
        ["content_hash"],
    )
    op.create_index(
        "idx_emotion_trajectories_trajectory_type",
        "emotion_trajectories",
        ["trajectory_type"],
    )
    op.create_index(
        "idx_emotion_trajectories_created_at", "emotion_trajectories", ["created_at"]
    )

    # Composite indexes for common queries
    op.create_index(
        "idx_emotion_trajectories_persona_trajectory",
        "emotion_trajectories",
        ["persona_id", "trajectory_type"],
    )
    op.create_index(
        "idx_emotion_trajectories_post_created",
        "emotion_trajectories",
        ["post_id", "created_at"],
    )

    # Create emotion_segments table for detailed segment-level analysis
    op.create_table(
        "emotion_segments",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("trajectory_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "segment_index", sa.Integer(), nullable=False
        ),  # 0-based segment position
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("sentence_count", sa.Integer(), nullable=False),
        # Segment-level emotions (BERT outputs)
        sa.Column("joy_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("anger_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fear_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sadness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("surprise_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("disgust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "anticipation_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Segment-level sentiment (VADER outputs)
        sa.Column(
            "sentiment_compound", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_positive", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_neutral", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "sentiment_negative", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Analysis metadata
        sa.Column("dominant_emotion", sa.String(length=20), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_peak", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_valley", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["trajectory_id"], ["emotion_trajectories.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for emotion_segments
    op.create_index(
        "idx_emotion_segments_trajectory_id", "emotion_segments", ["trajectory_id"]
    )
    op.create_index(
        "idx_emotion_segments_trajectory_segment",
        "emotion_segments",
        ["trajectory_id", "segment_index"],
    )
    op.create_index(
        "idx_emotion_segments_dominant_emotion",
        "emotion_segments",
        ["dominant_emotion"],
    )
    op.create_index("idx_emotion_segments_peaks", "emotion_segments", ["is_peak"])
    op.create_index("idx_emotion_segments_valleys", "emotion_segments", ["is_valley"])

    # Create emotion_transitions table for transition pattern analysis
    op.create_table(
        "emotion_transitions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("trajectory_id", sa.BigInteger(), nullable=False),
        sa.Column("from_segment_index", sa.Integer(), nullable=False),
        sa.Column("to_segment_index", sa.Integer(), nullable=False),
        sa.Column("from_emotion", sa.String(length=20), nullable=False),
        sa.Column("to_emotion", sa.String(length=20), nullable=False),
        sa.Column(
            "transition_type", sa.String(length=30), nullable=False
        ),  # strengthening, weakening, switching
        sa.Column("intensity_change", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "transition_speed", sa.Float(), nullable=False, server_default="0.0"
        ),  # change per word
        sa.Column("strength_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["trajectory_id"], ["emotion_trajectories.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for emotion_transitions
    op.create_index(
        "idx_emotion_transitions_trajectory_id",
        "emotion_transitions",
        ["trajectory_id"],
    )
    op.create_index(
        "idx_emotion_transitions_from_to",
        "emotion_transitions",
        ["from_emotion", "to_emotion"],
    )
    op.create_index(
        "idx_emotion_transitions_type", "emotion_transitions", ["transition_type"]
    )
    op.create_index(
        "idx_emotion_transitions_strength", "emotion_transitions", ["strength_score"]
    )

    # Create emotion_templates table for reusable emotion patterns
    op.create_table(
        "emotion_templates",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("template_name", sa.String(length=100), nullable=False),
        sa.Column(
            "template_type", sa.String(length=30), nullable=False
        ),  # curiosity_arc, controversy_wave, inspiration_journey
        sa.Column("pattern_description", sa.Text(), nullable=False),
        sa.Column("segment_count", sa.Integer(), nullable=False),
        sa.Column("optimal_duration_words", sa.Integer(), nullable=False),
        # Template characteristics
        sa.Column("trajectory_pattern", sa.String(length=20), nullable=False),
        sa.Column(
            "primary_emotions", postgresql.ARRAY(sa.String), nullable=False
        ),  # Array of emotion names
        sa.Column(
            "emotion_sequence", sa.Text(), nullable=False
        ),  # JSON string of emotion progression
        sa.Column(
            "transition_patterns", sa.Text(), nullable=False
        ),  # JSON string of transition rules
        # Performance metrics
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "average_engagement", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "engagement_correlation", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "effectiveness_score", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Version control
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "template_name", "version", name="uq_emotion_templates_name_version"
        ),
    )

    # Create indexes for emotion_templates
    op.create_index(
        "idx_emotion_templates_name", "emotion_templates", ["template_name"]
    )
    op.create_index(
        "idx_emotion_templates_type", "emotion_templates", ["template_type"]
    )
    op.create_index("idx_emotion_templates_active", "emotion_templates", ["is_active"])
    op.create_index(
        "idx_emotion_templates_effectiveness",
        "emotion_templates",
        ["effectiveness_score"],
    )
    op.create_index("idx_emotion_templates_usage", "emotion_templates", ["usage_count"])

    # Create emotion_performance table for tracking emotion-engagement correlations
    op.create_table(
        "emotion_performance",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("trajectory_id", sa.BigInteger(), nullable=False),
        sa.Column("post_id", sa.String(length=100), nullable=False),
        sa.Column("persona_id", sa.String(length=50), nullable=False),
        # Engagement metrics
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("likes_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shares_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        # Performance correlation
        sa.Column(
            "emotion_effectiveness", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "predicted_engagement", sa.Float(), nullable=False, server_default="0.0"
        ),
        sa.Column(
            "actual_vs_predicted", sa.Float(), nullable=False, server_default="0.0"
        ),
        # Time tracking
        sa.Column("measured_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["trajectory_id"], ["emotion_trajectories.id"], ondelete="CASCADE"
        ),
    )

    # Create indexes for emotion_performance
    op.create_index(
        "idx_emotion_performance_trajectory_id",
        "emotion_performance",
        ["trajectory_id"],
    )
    op.create_index(
        "idx_emotion_performance_post_id", "emotion_performance", ["post_id"]
    )
    op.create_index(
        "idx_emotion_performance_persona_id", "emotion_performance", ["persona_id"]
    )
    op.create_index(
        "idx_emotion_performance_engagement", "emotion_performance", ["engagement_rate"]
    )
    op.create_index(
        "idx_emotion_performance_measured_at", "emotion_performance", ["measured_at"]
    )

    # Composite indexes for analytics queries
    op.create_index(
        "idx_emotion_performance_persona_measured",
        "emotion_performance",
        ["persona_id", "measured_at"],
    )


def downgrade() -> None:
    # Drop indexes first, then tables (reverse order of creation)

    # emotion_performance indexes
    op.drop_index(
        "idx_emotion_performance_persona_measured", table_name="emotion_performance"
    )
    op.drop_index(
        "idx_emotion_performance_measured_at", table_name="emotion_performance"
    )
    op.drop_index(
        "idx_emotion_performance_engagement", table_name="emotion_performance"
    )
    op.drop_index(
        "idx_emotion_performance_persona_id", table_name="emotion_performance"
    )
    op.drop_index("idx_emotion_performance_post_id", table_name="emotion_performance")
    op.drop_index(
        "idx_emotion_performance_trajectory_id", table_name="emotion_performance"
    )

    # emotion_templates indexes
    op.drop_index("idx_emotion_templates_usage", table_name="emotion_templates")
    op.drop_index("idx_emotion_templates_effectiveness", table_name="emotion_templates")
    op.drop_index("idx_emotion_templates_active", table_name="emotion_templates")
    op.drop_index("idx_emotion_templates_type", table_name="emotion_templates")
    op.drop_index("idx_emotion_templates_name", table_name="emotion_templates")

    # emotion_transitions indexes
    op.drop_index("idx_emotion_transitions_strength", table_name="emotion_transitions")
    op.drop_index("idx_emotion_transitions_type", table_name="emotion_transitions")
    op.drop_index("idx_emotion_transitions_from_to", table_name="emotion_transitions")
    op.drop_index(
        "idx_emotion_transitions_trajectory_id", table_name="emotion_transitions"
    )

    # emotion_segments indexes
    op.drop_index("idx_emotion_segments_valleys", table_name="emotion_segments")
    op.drop_index("idx_emotion_segments_peaks", table_name="emotion_segments")
    op.drop_index(
        "idx_emotion_segments_dominant_emotion", table_name="emotion_segments"
    )
    op.drop_index(
        "idx_emotion_segments_trajectory_segment", table_name="emotion_segments"
    )
    op.drop_index("idx_emotion_segments_trajectory_id", table_name="emotion_segments")

    # emotion_trajectories indexes
    op.drop_index(
        "idx_emotion_trajectories_post_created", table_name="emotion_trajectories"
    )
    op.drop_index(
        "idx_emotion_trajectories_persona_trajectory", table_name="emotion_trajectories"
    )
    op.drop_index(
        "idx_emotion_trajectories_created_at", table_name="emotion_trajectories"
    )
    op.drop_index(
        "idx_emotion_trajectories_trajectory_type", table_name="emotion_trajectories"
    )
    op.drop_index(
        "idx_emotion_trajectories_content_hash", table_name="emotion_trajectories"
    )
    op.drop_index(
        "idx_emotion_trajectories_persona_id", table_name="emotion_trajectories"
    )
    op.drop_index("idx_emotion_trajectories_post_id", table_name="emotion_trajectories")

    # Drop tables (reverse order due to foreign key constraints)
    op.drop_table("emotion_performance")
    op.drop_table("emotion_templates")
    op.drop_table("emotion_transitions")
    op.drop_table("emotion_segments")
    op.drop_table("emotion_trajectories")
