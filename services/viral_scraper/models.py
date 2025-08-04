# services/viral_scraper/models.py
"""
Data models for viral content scraper service.

Minimal implementation to pass initial tests.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class ViralPost(BaseModel):
    """Model for viral post data scraped from Threads accounts"""

    # Content fields
    content: str = Field(..., description="Post content text")
    account_id: str = Field(..., description="Threads account identifier")
    post_url: str = Field(..., description="URL to the original post")
    timestamp: datetime = Field(..., description="When the post was created")

    # Engagement metrics
    likes: int = Field(..., ge=0, description="Number of likes")
    comments: int = Field(..., ge=0, description="Number of comments")
    shares: int = Field(..., ge=0, description="Number of shares")
    engagement_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Engagement rate (0-1)"
    )

    # Performance analysis
    performance_percentile: float = Field(
        ..., ge=0.0, le=100.0, description="Performance percentile (0-100)"
    )

    def is_top_1_percent(self) -> bool:
        """Check if this post is in the top 1% performance tier"""
        return self.performance_percentile > 99.0
