"""
Achievement-based Content Generator

Generates articles and technical content from achievements stored in the
achievement_collector service.
"""

from typing import List, Dict, Any
import structlog

from ..models.article import ArticleType, Platform, ArticleContent
from ..clients.achievement_client import AchievementClient, Achievement
from .content_generator import ContentGenerator
from ..core.config import get_settings

logger = structlog.get_logger()


class AchievementContentGenerator:
    """
    Generates various types of content from achievements.

    This service bridges the achievement_collector and tech_doc_generator
    to create automated content from your professional achievements.
    """

    def __init__(self):
        self.achievement_client = AchievementClient()
        self.content_generator = ContentGenerator()
        self.settings = get_settings()

    async def generate_from_achievement(
        self,
        achievement_id: int,
        article_types: List[ArticleType],
        platforms: List[Platform],
    ) -> List[ArticleContent]:
        """
        Generate multiple article variations from a single achievement.

        Args:
            achievement_id: ID of the achievement to use
            article_types: Types of articles to generate
            platforms: Target platforms for content

        Returns:
            List of generated article content
        """
        try:
            # Fetch achievement data
            async with self.achievement_client as client:
                achievement = await client.get_achievement(achievement_id)

            if not achievement:
                logger.warning("achievement_not_found", achievement_id=achievement_id)
                return []

            logger.info(
                "generating_content_from_achievement",
                achievement_id=achievement_id,
                title=achievement.title,
                impact_score=achievement.impact_score,
            )

            # Convert achievement to analysis format
            analysis = self._achievement_to_analysis(achievement)

            # Generate content for each type and platform combination
            generated_content = []
            for article_type in article_types:
                for platform in platforms:
                    content = await self.content_generator.generate_article(
                        analysis, article_type, platform
                    )
                    content.metadata["achievement_id"] = achievement_id
                    content.metadata["achievement_impact_score"] = (
                        achievement.impact_score
                    )
                    generated_content.append(content)

            logger.info(
                "content_generated_from_achievement",
                achievement_id=achievement_id,
                articles_count=len(generated_content),
            )

            return generated_content

        except Exception as e:
            logger.error(
                "achievement_content_generation_failed",
                achievement_id=achievement_id,
                error=str(e),
            )
            raise

    async def generate_weekly_highlights(
        self, platforms: List[Platform] = None
    ) -> List[ArticleContent]:
        """
        Generate content from the week's top achievements.

        Args:
            platforms: Target platforms (defaults to all supported)

        Returns:
            List of generated articles
        """
        if platforms is None:
            platforms = [Platform.LINKEDIN, Platform.DEVTO, Platform.MEDIUM]

        try:
            async with self.achievement_client as client:
                # Get recent high-impact achievements using optimized endpoint
                achievements = await client.get_recent_highlights(
                    days=7, min_impact_score=75.0, limit=10
                )

            if not achievements:
                logger.warning("no_recent_achievements_found")
                return []

            logger.info(
                "generating_weekly_highlights", achievements_count=len(achievements)
            )

            # Generate content for top 3 achievements
            all_content = []
            for achievement in achievements[:3]:
                # Different article types for different achievements
                if achievement.impact_score >= 90:
                    article_types = [ArticleType.CASE_STUDY, ArticleType.DEEP_DIVE]
                elif achievement.impact_score >= 80:
                    article_types = [ArticleType.TUTORIAL, ArticleType.BEST_PRACTICES]
                else:
                    article_types = [ArticleType.LESSONS_LEARNED, ArticleType.QUICK_TIP]

                content = await self.generate_from_achievement(
                    achievement.id, article_types, platforms
                )
                all_content.extend(content)

            return all_content

        except Exception as e:
            logger.error("weekly_highlights_generation_failed", error=str(e))
            raise

    async def generate_company_specific_content(
        self, company_name: str, achievement_categories: List[str] = None
    ) -> List[ArticleContent]:
        """
        Generate content targeted at a specific company.

        Args:
            company_name: Target company (e.g., "notion", "jasper")
            achievement_categories: Categories to focus on

        Returns:
            List of company-targeted articles
        """
        # Company-specific content strategies
        company_profiles = {
            "notion": {
                "focus": ["productivity", "automation", "ai"],
                "platforms": [Platform.LINKEDIN, Platform.MEDIUM],
                "article_types": [
                    ArticleType.CASE_STUDY,
                    ArticleType.TECHNICAL_DEEP_DIVE,
                ],
            },
            "jasper": {
                "focus": ["content-generation", "ai", "scalability"],
                "platforms": [Platform.LINKEDIN, Platform.DEVTO],
                "article_types": [
                    ArticleType.ARCHITECTURE_OVERVIEW,
                    ArticleType.PERFORMANCE_OPTIMIZATION,
                ],
            },
            "anthropic": {
                "focus": ["ai-safety", "monitoring", "responsible-ai"],
                "platforms": [Platform.MEDIUM, Platform.GITHUB],
                "article_types": [
                    ArticleType.BEST_PRACTICES,
                    ArticleType.SECURITY_ANALYSIS,
                ],
            },
        }

        profile = company_profiles.get(company_name.lower())
        if not profile:
            logger.warning("unknown_company_profile", company=company_name)
            return []

        try:
            async with self.achievement_client as client:
                # Get achievements matching company focus using optimized endpoint
                categories = achievement_categories or profile["focus"]
                all_achievements = await client.get_company_targeted(
                    company_name=company_name, categories=categories, limit=20
                )

            # Remove duplicates and sort by impact
            unique_achievements = list({a.id: a for a in all_achievements}.values())
            unique_achievements.sort(key=lambda x: x.impact_score, reverse=True)

            # Generate targeted content
            content = []
            for achievement in unique_achievements[:3]:
                articles = await self.generate_from_achievement(
                    achievement.id, profile["article_types"], profile["platforms"]
                )

                # Add company-specific metadata
                for article in articles:
                    article.metadata["target_company"] = company_name
                    article.metadata["company_focus_match"] = True

                content.extend(articles)

            logger.info(
                "company_specific_content_generated",
                company=company_name,
                articles_count=len(content),
            )

            return content

        except Exception as e:
            logger.error(
                "company_content_generation_failed", company=company_name, error=str(e)
            )
            raise

    def _achievement_to_analysis(self, achievement: Achievement) -> Dict[str, Any]:
        """
        Convert achievement data to code analysis format expected by content generator.
        """
        return {
            "type": "achievement",
            "source_path": f"achievement_{achievement.id}",
            "complexity_score": achievement.impact_score,
            "key_insights": [
                {
                    "type": "business_impact",
                    "description": achievement.business_value
                    or achievement.description,
                    "importance": achievement.impact_score / 100,
                }
            ],
            "technical_details": achievement.technical_details or {},
            "patterns": {
                "category": achievement.category,
                "tags": achievement.tags,
                "metrics": achievement.metrics or {},
            },
            "metadata": {
                "title": achievement.title,
                "created_at": achievement.created_at.isoformat()
                if achievement.created_at
                else None,
                "portfolio_ready": achievement.portfolio_ready,
            },
        }
