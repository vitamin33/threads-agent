"""Database models for performance monitoring."""

from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class VariantMonitoring(Base):
    """Tracks monitoring sessions for variants."""

    __tablename__ = "variant_monitoring"

    id = Column(Integer, primary_key=True)
    variant_id = Column(String, nullable=False, index=True)
    persona_id = Column(String, nullable=False)
    post_id = Column(String, nullable=True)

    # Monitoring parameters
    expected_engagement_rate = Column(Float, nullable=False)
    kill_threshold = Column(Float, default=0.5)  # 50% of expected
    min_interactions = Column(Integer, default=10)

    # Timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    timeout_minutes = Column(Integer, default=10)

    # Status
    is_active = Column(Boolean, default=True)
    was_killed = Column(Boolean, default=False)
    kill_reason = Column(String, nullable=True)

    # Performance snapshot at decision time
    final_engagement_rate = Column(Float, nullable=True)
    final_interaction_count = Column(Integer, nullable=True)
    final_view_count = Column(Integer, nullable=True)

    # Metadata
    monitoring_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
