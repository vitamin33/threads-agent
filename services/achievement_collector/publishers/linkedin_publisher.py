"""LinkedIn achievement publisher using OAuth 2.0."""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import httpx
from sqlalchemy.orm import Session

from ..db.models import Achievement
from ..core.logging import setup_logging
from ..services.ai_analyzer import AIAnalyzer

logger = setup_logging(__name__)


class LinkedInPublisher:
    """Publishes achievements to LinkedIn as posts."""

    def __init__(self):
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.person_urn = os.getenv(
            "LINKEDIN_PERSON_URN"
        )  # Format: urn:li:person:xxxxx
        self.api_base = "https://api.linkedin.com/v2"
        self.ai_analyzer = AIAnalyzer()

    def is_configured(self) -> bool:
        """Check if LinkedIn credentials are configured."""
        return all([self.access_token, self.person_urn])

    async def publish_achievement(self, achievement: Achievement) -> Optional[str]:
        """Publish a single achievement to LinkedIn."""
        if not self.is_configured():
            logger.error("LinkedIn credentials not configured")
            return None

        try:
            # Generate LinkedIn post content
            post_content = await self._generate_post_content(achievement)

            # Create LinkedIn share
            post_id = await self._create_linkedin_post(post_content)

            if post_id:
                logger.info(
                    f"Published achievement {achievement.id} to LinkedIn: {post_id}"
                )
                return post_id
            else:
                logger.error(f"Failed to publish achievement {achievement.id}")
                return None

        except Exception as e:
            logger.error(f"Error publishing to LinkedIn: {e}")
            return None

    async def _generate_post_content(self, achievement: Achievement) -> Dict:
        """Generate LinkedIn post content from achievement."""
        # Use AI to generate engaging post text
        post_text = await self.ai_analyzer.generate_linkedin_content(achievement)

        # Fallback if AI fails
        if not post_text:
            post_text = self._generate_fallback_post(achievement)

        # Add achievement metrics
        if achievement.metrics_after:
            metrics_text = self._format_metrics(achievement.metrics_after)
            post_text += f"\n\n📊 Key Metrics:\n{metrics_text}"

        return {
            "text": post_text,
            "achievement_id": achievement.id,
            "category": achievement.category,
        }

    def _generate_fallback_post(self, achievement: Achievement) -> str:
        """Generate fallback post if AI is unavailable."""
        skills_text = " • ".join(achievement.skills_demonstrated[:5])

        post = f"""🚀 {achievement.title}

{achievement.description[:500]}...

💡 Technologies used: {skills_text}

#SoftwareEngineering #{achievement.category.title()} #TechAchievement #ContinuousLearning"""

        return post[:1300]  # LinkedIn limit

    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics for display."""
        formatted = []

        # Common metric formatting
        if "lines_added" in metrics:
            formatted.append(f"• {metrics['lines_added']:,} lines of code added")
        if "test_coverage" in metrics:
            formatted.append(f"• {metrics['test_coverage']}% test coverage")
        if "performance_improvement" in metrics:
            formatted.append(
                f"• {metrics['performance_improvement']}% performance boost"
            )
        if "issues_resolved" in metrics:
            formatted.append(f"• {metrics['issues_resolved']} issues resolved")

        return "\n".join(formatted[:3])  # Limit to 3 metrics

    async def _create_linkedin_post(self, content: Dict) -> Optional[str]:
        """Create a LinkedIn post using the API."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        # LinkedIn UGC Post API payload
        payload = {
            "author": self.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content["text"]},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base}/ugcPosts", headers=headers, json=payload
                )

                if response.status_code == 201:
                    post_id = response.headers.get("X-RestLi-Id")
                    return post_id
                else:
                    logger.error(
                        f"LinkedIn API error: {response.status_code} - {response.text}"
                    )
                    return None

            except Exception as e:
                logger.error(f"Error calling LinkedIn API: {e}")
                return None

    async def get_recent_posts(self, limit: int = 10) -> List[Dict]:
        """Get recent posts to avoid duplicates."""
        if not self.is_configured():
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        params = {"q": "authors", "authors": self.person_urn, "count": limit}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_base}/ugcPosts", headers=headers, params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("elements", [])
                else:
                    logger.error(f"Error fetching posts: {response.status_code}")
                    return []

            except Exception as e:
                logger.error(f"Error fetching recent posts: {e}")
                return []

    def should_publish(
        self, achievement: Achievement, recent_posts: List[Dict]
    ) -> bool:
        """Determine if achievement should be published."""
        # Check if portfolio ready
        if not achievement.portfolio_ready:
            return False

        # Check impact score threshold
        if achievement.impact_score < 70:
            return False

        # Check for recent similar posts
        for post in recent_posts:
            # Check if we've already posted about this achievement
            post_text = (
                post.get("specificContent", {})
                .get("com.linkedin.ugc.ShareContent", {})
                .get("shareCommentary", {})
                .get("text", "")
            )
            if achievement.title in post_text:
                logger.info(f"Achievement {achievement.id} already posted recently")
                return False

        return True

    async def publish_batch(self, db: Session, limit: int = 3):
        """Publish a batch of achievements."""
        if not self.is_configured():
            logger.warning("LinkedIn not configured, skipping batch publish")
            return

        # Get recent posts to avoid duplicates
        recent_posts = await self.get_recent_posts()

        # Get unpublished achievements
        unpublished = (
            db.query(Achievement)
            .filter(
                Achievement.portfolio_ready.is_(True),
                Achievement.linkedin_post_id.is_(None),
                Achievement.impact_score >= 70,
            )
            .order_by(Achievement.impact_score.desc())
            .limit(limit * 2)
            .all()
        )  # Get extra in case some are filtered

        published_count = 0
        for achievement in unpublished:
            if published_count >= limit:
                break

            if self.should_publish(achievement, recent_posts):
                post_id = await self.publish_achievement(achievement)
                if post_id:
                    # Update achievement with LinkedIn post ID
                    achievement.linkedin_post_id = post_id
                    achievement.linkedin_published_at = datetime.now()
                    db.commit()
                    published_count += 1

                    # Add delay between posts
                    if published_count < limit:
                        await asyncio.sleep(60)  # 1 minute between posts

        logger.info(f"Published {published_count} achievements to LinkedIn")
