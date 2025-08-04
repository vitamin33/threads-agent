"""
Shared models for cross-service communication
"""

from .achievement_models import (
    Achievement,
    AchievementCreate,
    AchievementUpdate,
    AchievementSummary,
    AchievementFilter,
    AchievementCategory,
    AchievementMetrics
)

from .article_models import (
    ArticleType,
    Platform,
    ArticleContent,
    ArticleMetadata,
    InsightScore,
    ContentRequest,
    ContentResponse
)

__all__ = [
    # Achievement models
    "Achievement",
    "AchievementCreate",
    "AchievementUpdate",
    "AchievementSummary",
    "AchievementFilter",
    "AchievementCategory",
    "AchievementMetrics",
    
    # Article models
    "ArticleType",
    "Platform",
    "ArticleContent",
    "ArticleMetadata",
    "InsightScore",
    "ContentRequest",
    "ContentResponse"
]