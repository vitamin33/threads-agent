# /services/orchestrator/db/models.py
from datetime import datetime, timezone
from typing import Any, List

from sqlalchemy import (
    BigInteger,
    Text,
    func,
    JSON,
    Integer,
    Float,
    String,
    Boolean,
    ForeignKey,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects import postgresql
from sqlalchemy import event
import json
import re

from . import Base


# Database compatibility layer for ARRAY type
class ArrayType(TypeDecorator):
    """Custom type that uses ARRAY for PostgreSQL and JSON for SQLite."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(String))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql":
            # For SQLite, convert list to JSON string
            return json.dumps(value) if isinstance(value, list) else value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name != "postgresql" and isinstance(value, str):
            # For SQLite, parse JSON string back to list
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value


def get_array_type(item_type):
    """Return custom ArrayType that works with both PostgreSQL and SQLite."""
    return ArrayType()


def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title."""
    # Convert to lowercase, replace spaces with hyphens
    slug = title.lower().strip()
    # Remove special characters
    slug = re.sub(r"[^\w\s-]", "", slug)
    # Replace spaces with hyphens
    slug = re.sub(r"[-\s]+", "-", slug)
    # Remove leading/trailing hyphens
    slug = slug.strip("-")
    return slug[:200]  # Limit to 200 chars


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    persona_id: Mapped[str] = mapped_column(
        Text, index=True
    )  # Add index for faster filtering
    hook: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    tokens_used: Mapped[int] = mapped_column(default=0)
    ts: Mapped[datetime] = mapped_column(
        default=func.now(), index=True
    )  # Add index for time-based queries
    engagement_rate: Mapped[float] = mapped_column(
        default=0.0, index=True
    )  # Add engagement tracking with index
    original_input: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # Store original input for training


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payload: Mapped[dict[str, Any]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="queued")


class VariantPerformance(Base):
    __tablename__ = "variant_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    variant_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    dimensions: Mapped[dict[str, str]] = mapped_column(JSON)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    successes: Mapped[int] = mapped_column(Integer, default=0)
    last_used: Mapped[datetime] = mapped_column(default=func.now())
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    @hybrid_property
    def success_rate(self) -> float:
        """Calculate success rate avoiding division by zero."""
        if self.impressions == 0:
            return 0.0
        return self.successes / self.impressions


class EmotionTrajectory(Base):
    """Store emotion analysis results for content pieces."""

    __tablename__ = "emotion_trajectories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_duration_words: Mapped[int] = mapped_column(Integer, nullable=False)
    analysis_model: Mapped[str] = mapped_column(
        String(50), nullable=False, default="bert_vader"
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Trajectory characteristics
    trajectory_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    emotional_variance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    peak_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valley_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Primary emotions (BERT model outputs)
    joy_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anger_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fear_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sadness_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    surprise_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disgust_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trust_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anticipation_avg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Sentiment analysis (VADER outputs)
    sentiment_compound: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    sentiment_positive: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    sentiment_neutral: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_negative: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Performance metrics
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    segments: Mapped[List["EmotionSegment"]] = relationship(
        "EmotionSegment", back_populates="trajectory", cascade="all, delete-orphan"
    )
    transitions: Mapped[List["EmotionTransition"]] = relationship(
        "EmotionTransition", back_populates="trajectory", cascade="all, delete-orphan"
    )
    performance: Mapped[List["EmotionPerformance"]] = relationship(
        "EmotionPerformance", back_populates="trajectory", cascade="all, delete-orphan"
    )

    @hybrid_property
    def dominant_emotion(self) -> str:
        """Get the dominant emotion from averages."""
        emotions = {
            "joy": self.joy_avg,
            "anger": self.anger_avg,
            "fear": self.fear_avg,
            "sadness": self.sadness_avg,
            "surprise": self.surprise_avg,
            "disgust": self.disgust_avg,
            "trust": self.trust_avg,
            "anticipation": self.anticipation_avg,
        }
        return max(emotions, key=emotions.get)


class EmotionSegment(Base):
    """Store detailed segment-level emotion analysis."""

    __tablename__ = "emotion_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trajectory_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("emotion_trajectories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sentence_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Segment-level emotions (BERT outputs)
    joy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anger_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fear_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sadness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    surprise_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disgust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    anticipation_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Segment-level sentiment (VADER outputs)
    sentiment_compound: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    sentiment_positive: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    sentiment_neutral: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sentiment_negative: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Analysis metadata
    dominant_emotion: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_peak: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    is_valley: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    trajectory: Mapped["EmotionTrajectory"] = relationship(
        "EmotionTrajectory", back_populates="segments"
    )


class EmotionTransition(Base):
    """Store emotion transition patterns between segments."""

    __tablename__ = "emotion_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trajectory_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("emotion_trajectories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    to_segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    from_emotion: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    to_emotion: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    transition_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    intensity_change: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transition_speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    strength_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    trajectory: Mapped["EmotionTrajectory"] = relationship(
        "EmotionTrajectory", back_populates="transitions"
    )


class EmotionTemplate(Base):
    """Store reusable emotion pattern templates."""

    __tablename__ = "emotion_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    template_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    template_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    pattern_description: Mapped[str] = mapped_column(Text, nullable=False)
    segment_count: Mapped[int] = mapped_column(Integer, nullable=False)
    optimal_duration_words: Mapped[int] = mapped_column(Integer, nullable=False)

    # Template characteristics
    trajectory_pattern: Mapped[str] = mapped_column(String(20), nullable=False)
    primary_emotions: Mapped[List[str]] = mapped_column(
        get_array_type(String), nullable=False
    )
    emotion_sequence: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    transition_patterns: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON string

    # Performance metrics
    usage_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, index=True
    )
    average_engagement: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    engagement_correlation: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    effectiveness_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )

    # Version control
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )


class EmotionPerformance(Base):
    """Track emotion-engagement correlations and performance metrics."""

    __tablename__ = "emotion_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trajectory_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("emotion_trajectories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    post_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Engagement metrics
    engagement_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )
    likes_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Performance correlation
    emotion_effectiveness: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    predicted_engagement: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    actual_vs_predicted: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Time tracking
    measured_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    trajectory: Mapped["EmotionTrajectory"] = relationship(
        "EmotionTrajectory", back_populates="performance"
    )


# Content Scheduler Models - Phase 1 of Epic 14


class ContentItem(Base):
    """Primary content storage with lifecycle management."""

    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    author_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )

    # Optional fields
    slug: Mapped[str] = mapped_column(
        String(200), nullable=True, unique=True, index=True
    )
    content_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    schedules: Mapped[List["ContentSchedule"]] = relationship(
        "ContentSchedule", back_populates="content_item", cascade="all, delete-orphan"
    )
    analytics: Mapped[List["ContentAnalytics"]] = relationship(
        "ContentAnalytics", back_populates="content_item", cascade="all, delete-orphan"
    )


# Event listener to auto-generate slug before insert
@event.listens_for(ContentItem, "before_insert")
def generate_content_slug(mapper, connection, target):
    """Auto-generate slug from title if not provided."""
    if target.slug is None and target.title:
        target.slug = generate_slug(target.title)


class ContentSchedule(Base):
    """Multi-platform scheduling with timezone support."""

    __tablename__ = "content_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scheduled_time: Mapped[datetime] = mapped_column(nullable=False, index=True)
    timezone_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="UTC"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled", index=True
    )

    # Retry mechanism
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_time: Mapped[datetime] = mapped_column(nullable=True)

    # Platform-specific configuration
    platform_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Publish tracking
    published_at: Mapped[datetime] = mapped_column(nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem", back_populates="schedules"
    )


class ContentAnalytics(Base):
    """Performance tracking and analytics."""

    __tablename__ = "content_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("content_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Core metrics
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    engagement_rate: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )

    # Additional platform-specific metrics
    additional_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Time tracking
    measured_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    content_item: Mapped["ContentItem"] = relationship(
        "ContentItem", back_populates="analytics"
    )


# ── Experiment Management Models ──────────────────────────────────────────────


class Experiment(Base):
    """A/B testing experiment with lifecycle management."""

    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Experiment configuration
    variant_ids: Mapped[dict[str, Any]] = mapped_column(
        JSON
    )  # Store as JSON for compatibility
    traffic_allocation: Mapped[dict[str, Any]] = mapped_column(
        JSON
    )  # Store as JSON for compatibility
    control_variant_id: Mapped[str] = mapped_column(Text, nullable=True)
    target_persona: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    success_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSON
    )  # Store as JSON for compatibility

    # Experiment lifecycle
    status: Mapped[str] = mapped_column(
        Text, default="draft", index=True
    )  # draft, active, paused, completed, cancelled
    start_time: Mapped[datetime] = mapped_column(nullable=True, index=True)
    end_time: Mapped[datetime] = mapped_column(nullable=True, index=True)
    expected_end_time: Mapped[datetime] = mapped_column(nullable=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Statistical parameters
    min_sample_size: Mapped[int] = mapped_column(Integer, nullable=True)
    significance_level: Mapped[float] = mapped_column(Float, default=0.05)
    minimum_detectable_effect: Mapped[float] = mapped_column(Float, default=0.05)

    # Results tracking
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
    winner_variant_id: Mapped[str] = mapped_column(Text, nullable=True)
    improvement_percentage: Mapped[float] = mapped_column(Float, nullable=True)
    is_statistically_significant: Mapped[bool] = mapped_column(Boolean, default=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=True)

    # Metadata
    created_by: Mapped[str] = mapped_column(Text, nullable=True)
    experiment_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    experiment_events: Mapped[List["ExperimentEvent"]] = relationship(
        "ExperimentEvent", back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentEvent(Base):
    """Events related to experiment lifecycle and participant interactions."""

    __tablename__ = "experiment_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(
        Text, ForeignKey("experiments.experiment_id"), index=True
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        Text, nullable=False, index=True
    )  # participant_assigned, impression, engagement, etc.
    participant_id: Mapped[str] = mapped_column(
        Text, nullable=True, index=True
    )  # User/session ID
    variant_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    # Engagement data
    action_taken: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # like, share, comment, etc.
    engagement_value: Mapped[float] = mapped_column(Float, nullable=True)

    # Context
    event_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(default=func.now(), index=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment", back_populates="experiment_events"
    )


class ExperimentVariant(Base):
    """Performance tracking for specific variants within experiments."""

    __tablename__ = "experiment_variants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(
        Text, ForeignKey("experiments.experiment_id"), index=True
    )
    variant_id: Mapped[str] = mapped_column(
        Text, ForeignKey("variant_performance.variant_id"), index=True
    )

    # Traffic allocation
    allocated_traffic: Mapped[float] = mapped_column(
        Float, nullable=False
    )  # 0.0 to 1.0
    actual_traffic: Mapped[float] = mapped_column(
        Float, default=0.0
    )  # Actual traffic received

    # Performance within this experiment
    participants: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # Statistical data
    confidence_lower: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_upper: Mapped[float] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    @hybrid_property
    def traffic_deviation(self) -> float:
        """Calculate deviation from allocated traffic."""
        return abs(self.actual_traffic - self.allocated_traffic)


class ExperimentSegment(Base):
    """Segmented analysis results for experiments."""

    __tablename__ = "experiment_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(
        Text, ForeignKey("experiments.experiment_id"), index=True
    )

    # Segment definition
    segment_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    segment_filter: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False
    )  # Filter criteria

    # Segment performance
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
    variant_performance: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=True
    )  # Performance by variant

    # Statistical significance for this segment
    is_significant: Mapped[bool] = mapped_column(Boolean, default=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float] = mapped_column(Float, default=0.95)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
