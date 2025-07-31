from datetime import datetime
from sqlalchemy import Column, String, DateTime, BigInteger, Float, Index, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PatternUsage(Base):
    """Tracks pattern usage by personas over time."""

    __tablename__ = "pattern_usage"

    # Use Integer for SQLite compatibility in tests, BigInteger in production
    id = Column(Integer, primary_key=True, autoincrement=True)
    persona_id = Column(String(50), nullable=False)
    pattern_id = Column(String(100), nullable=False)
    post_id = Column(String(100), nullable=False)
    used_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    engagement_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_pattern_usage_persona_pattern", "persona_id", "pattern_id"),
        Index("idx_pattern_usage_used_at", "used_at"),
    )
