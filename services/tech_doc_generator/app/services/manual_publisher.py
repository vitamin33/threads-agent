"""Manual Publishing Workflow for Platforms with API Restrictions"""

import time
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.article import ArticleContent, Platform
from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger()


class ManualPublishingTracker:
    """Track manual publishing workflow for platforms like LinkedIn"""

    def __init__(self, db: Session):
        self.db = db

    async def create_draft(
        self, platform: Platform, content: ArticleContent, formatted_content: str
    ) -> Dict[str, Any]:
        """Create a draft for manual publishing"""

        draft_id = f"{platform.value}_draft_{int(time.time())}"

        # Store draft metadata (in production, this would go to database)
        draft_data = {
            "draft_id": draft_id,
            "platform": platform.value,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending_manual_post",
            "formatted_content": formatted_content,
            "metadata": {
                "title": content.title,
                "tags": content.tags,
                "insights": content.insights[:3] if content.insights else [],
            },
        }

        # Log the draft creation
        logger.info(
            "manual_draft_created",
            draft_id=draft_id,
            platform=platform.value,
            article_title=content.title,
        )

        return {
            "success": True,
            "draft_id": draft_id,
            "platform": platform.value,
            "content": formatted_content,
            "instructions": self._get_platform_instructions(platform),
            "tracking_url": f"/publish/drafts/{draft_id}",
        }

    async def confirm_manual_post(
        self,
        draft_id: str,
        post_url: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Confirm that content was manually posted"""

        # In production, retrieve draft from database
        # For now, parse draft_id
        platform = draft_id.split("_")[0]

        confirmation_data = {
            "draft_id": draft_id,
            "platform": platform,
            "posted_at": datetime.utcnow().isoformat(),
            "status": "manually_posted",
            "post_url": post_url,
            "screenshot_path": screenshot_path,
        }

        logger.info(
            "manual_post_confirmed",
            draft_id=draft_id,
            platform=platform,
            post_url=post_url,
        )

        # Trigger achievement tracking
        await self._track_achievement(confirmation_data)

        return {
            "success": True,
            "message": f"Post confirmed for {platform}",
            "tracking_enabled": True,
            "next_steps": [
                "Screenshot analytics after 24-48 hours",
                "Upload analytics via /publish/analytics endpoint",
                "AI will analyze performance for future improvements",
            ],
        }

    async def upload_analytics(
        self,
        draft_id: str,
        analytics_data: Dict[str, Any],
        screenshot_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload manual analytics for AI learning"""

        platform = draft_id.split("_")[0]

        # Process analytics based on platform
        processed_metrics = self._process_platform_analytics(platform, analytics_data)

        # Store for AI training
        analytics_record = {
            "draft_id": draft_id,
            "platform": platform,
            "captured_at": datetime.utcnow().isoformat(),
            "metrics": processed_metrics,
            "screenshot_path": screenshot_path,
        }

        logger.info(
            "manual_analytics_uploaded",
            draft_id=draft_id,
            platform=platform,
            metrics=processed_metrics,
        )

        # Feed to achievement collector for learning
        await self._feed_to_ai_learning(analytics_record)

        return {
            "success": True,
            "message": "Analytics uploaded successfully",
            "processed_metrics": processed_metrics,
            "ai_learning": "Metrics fed to AI for content optimization",
        }

    def _get_platform_instructions(self, platform: Platform) -> list:
        """Get platform-specific manual posting instructions"""

        instructions = {
            Platform.LINKEDIN: [
                "1. Copy the formatted content below",
                "2. Go to LinkedIn and click 'Start a post'",
                "3. Paste the content and review formatting",
                "4. Add any images or documents if needed",
                "5. Click 'Post' to publish",
                "6. Copy the post URL",
                "7. Call POST /publish/confirm with draft_id and post_url",
            ],
            Platform.TWITTER: [
                "1. Copy each tweet in the thread",
                "2. Go to Twitter/X and compose new tweet",
                "3. Post the first tweet",
                "4. Reply to it with subsequent tweets",
                "5. Copy the thread URL",
                "6. Call POST /publish/confirm with draft_id and post_url",
            ],
        }

        return instructions.get(
            platform, ["Platform-specific instructions not available"]
        )

    def _process_platform_analytics(
        self, platform: str, raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process platform-specific analytics data"""

        if platform == "linkedin":
            return {
                "impressions": raw_data.get("impressions", 0),
                "likes": raw_data.get("reactions", 0),
                "comments": raw_data.get("comments", 0),
                "shares": raw_data.get("reposts", 0),
                "engagement_rate": self._calculate_engagement_rate(raw_data),
                "click_through_rate": raw_data.get("ctr", 0),
            }
        elif platform == "twitter":
            return {
                "impressions": raw_data.get("impressions", 0),
                "likes": raw_data.get("likes", 0),
                "retweets": raw_data.get("retweets", 0),
                "replies": raw_data.get("replies", 0),
                "engagement_rate": self._calculate_engagement_rate(raw_data),
                "profile_visits": raw_data.get("profile_visits", 0),
            }
        else:
            return raw_data

    def _calculate_engagement_rate(self, metrics: Dict[str, Any]) -> float:
        """Calculate engagement rate from metrics"""
        impressions = metrics.get("impressions", 1)  # Avoid division by zero
        engagements = (
            metrics.get("likes", 0)
            + metrics.get("reactions", 0)
            + metrics.get("comments", 0)
            + metrics.get("shares", 0)
            + metrics.get("reposts", 0)
            + metrics.get("retweets", 0)
            + metrics.get("replies", 0)
        )
        return (engagements / impressions) * 100 if impressions > 0 else 0

    async def _track_achievement(self, confirmation_data: Dict[str, Any]):
        """Create achievement for manual post"""
        # This would integrate with achievement_collector service
        logger.info("achievement_tracked", data=confirmation_data)

    async def _feed_to_ai_learning(self, analytics_data: Dict[str, Any]):
        """Feed analytics to AI for content optimization"""
        # This would integrate with AI learning pipeline
        logger.info("ai_learning_fed", data=analytics_data)


class LinkedInManualWorkflow:
    """Specific workflow for LinkedIn manual posting"""

    @staticmethod
    def format_for_copy_paste(content: ArticleContent) -> str:
        """Format content optimized for LinkedIn copy-paste"""

        # Create compelling hook
        post = f"🚀 {content.title}\n\n"

        # Add story/context (LinkedIn loves stories)
        if "problem" in content.content.lower():
            post += "Here's a problem I recently solved:\n\n"

        # Key insights with emojis for visual appeal
        if content.insights:
            for i, insight in enumerate(content.insights[:3]):
                emoji = ["💡", "🔧", "📊"][i % 3]
                post += f"{emoji} {insight}\n\n"

        # Brief content summary
        summary_length = 800  # LinkedIn optimal length
        if len(content.content) > summary_length:
            # Find a good break point
            summary = content.content[:summary_length]
            last_period = summary.rfind(".")
            if last_period > 600:
                summary = summary[: last_period + 1]
            post += f"{summary}\n\n"
        else:
            post += f"{content.content}\n\n"

        # Call to action
        post += (
            "💭 What's your experience with this? I'd love to hear your thoughts!\n\n"
        )

        # Hashtags (LinkedIn Algorithm favors 3-5 hashtags)
        hashtags = [
            "#TechLeadership",
            "#SoftwareEngineering",
            "#AI",
            "#MLOps",
            "#Innovation",
        ]
        if content.tags:
            # Add specific tags
            for tag in content.tags[:2]:
                hashtag = f"#{tag.replace(' ', '').replace('-', '')}"
                if hashtag not in hashtags:
                    hashtags.insert(0, hashtag)

        post += " ".join(hashtags[:5])

        return post

    @staticmethod
    def create_analytics_template() -> Dict[str, Any]:
        """Template for manually entering LinkedIn analytics"""

        return {
            "platform": "linkedin",
            "metrics_template": {
                "impressions": "Number shown in post analytics",
                "reactions": "Total reactions (likes, celebrate, etc)",
                "comments": "Number of comments",
                "reposts": "Number of reposts/shares",
                "ctr": "Click-through rate if available",
                "profile_views": "Profile views from post",
            },
            "example": {
                "impressions": 1250,
                "reactions": 47,
                "comments": 8,
                "reposts": 3,
                "ctr": 2.4,
                "profile_views": 23,
            },
            "instructions": [
                "Wait 24-48 hours after posting",
                "Go to your LinkedIn post",
                "Click on analytics/stats",
                "Fill in the metrics above",
                "Take a screenshot for verification",
            ],
        }
