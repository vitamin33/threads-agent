"""
Database models for FinOps Engine cost attribution system.

Defines the PostCostAnalysis model for storing per-post cost data
with high accuracy and complete audit trail requirements.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class PostCostAnalysis(Base):
    """
    Database model for storing per-post cost attribution data.

    Supports 95% accuracy target with complete audit trail for
    tracking costs from generation through publication.
    """

    __tablename__ = "post_cost_analysis"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core cost attribution fields
    post_id = Column(String(255), nullable=False, index=True)
    cost_type = Column(String(100), nullable=False, index=True)
    cost_amount = Column(Float, nullable=False)

    # Metadata for audit trail and accuracy calculation
    cost_metadata = Column(JSONB, nullable=True)
    accuracy_score = Column(Float, nullable=False, default=0.95)

    # Timestamps for audit trail
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Create composite indexes for performance
    __table_args__ = (
        Index("idx_post_cost_analysis_post_id_created", "post_id", "created_at"),
        Index("idx_post_cost_analysis_cost_type_created", "cost_type", "created_at"),
    )
