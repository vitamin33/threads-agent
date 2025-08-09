"""
Weekly Content Generation Scheduler

Automated system that generates and schedules professional AI job content
using achievements from achievement_collector and viral optimization from viral_engine.

Key Features:
- Automated weekly content generation (3+ posts per week)
- Multi-platform publishing (LinkedIn, Medium, Dev.to)
- Company-targeted content for job applications
- Performance tracking and optimization
- Quality gates and engagement prediction
"""

from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog
from pydantic import BaseModel, Field

from ..clients.achievement_client import AchievementClient
from .professional_content_engine import (
    ProfessionalContentEngine,
    ProfessionalContentRequest,
    ProfessionalContentResult,
)
from .achievement_content_generator import ContentType, Platform

logger = structlog.get_logger()


class ScheduleFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"


class ContentScheduleEntry(BaseModel):
    """Single scheduled content entry"""

    id: str
    achievement_id: int
    content_type: ContentType
    platform: Platform
    target_company: Optional[str] = None
    scheduled_time: datetime
    status: str = "scheduled"  # scheduled, generated, published, failed
    generated_content: Optional[ProfessionalContentResult] = None
    created_at: datetime = Field(default_factory=datetime.now)


class WeeklyContentPlan(BaseModel):
    """Weekly content generation plan"""

    week_start: datetime
    target_posts: int = 3
    platforms: List[Platform] = Field(
        default_factory=lambda: [Platform.LINKEDIN, Platform.MEDIUM, Platform.DEVTO]
    )
    target_companies: List[str] = Field(
        default_factory=lambda: ["anthropic", "notion", "stripe"]
    )
    content_types: List[ContentType] = Field(
        default_factory=lambda: [
            ContentType.CASE_STUDY,
            ContentType.LINKEDIN_POST,
            ContentType.TECHNICAL_BLOG,
        ]
    )
    scheduled_entries: List[ContentScheduleEntry] = Field(default_factory=list)


class ContentScheduler:
    """
    Automated content scheduler that generates professional AI job content
    on a weekly schedule using the best achievements and viral optimization.

    Weekly Schedule:
    - Monday: Technical case study (LinkedIn)
    - Wednesday: Industry insight post (Medium)
    - Friday: Problem-solving story (Dev.to)

    Company Targeting:
    - Rotates content focus between target companies
    - Optimizes achievements selection for company relevance
    - Tracks application-related engagement
    """

    def __init__(self):
        self.achievement_client = AchievementClient()
        self.content_engine = ProfessionalContentEngine()
        self.active_schedules: Dict[str, WeeklyContentPlan] = {}

        # Optimal posting times for professional audience
        self.posting_schedule = {
            Platform.LINKEDIN: {
                "monday": time(10, 0),  # Monday 10 AM - start week strong
                "wednesday": time(14, 0),  # Wednesday 2 PM - mid-week engagement
                "friday": time(11, 0),  # Friday 11 AM - end week insights
            },
            Platform.MEDIUM: {
                "tuesday": time(19, 0),  # Tuesday 7 PM - evening reading
                "thursday": time(20, 0),  # Thursday 8 PM - deep content
                "sunday": time(18, 0),  # Sunday 6 PM - weekend prep
            },
            Platform.DEVTO: {
                "wednesday": time(15, 0),  # Wednesday 3 PM - technical focus
                "friday": time(16, 0),  # Friday 4 PM - weekend projects
                "saturday": time(10, 0),  # Saturday 10 AM - community time
            },
        }

        # Content type rotation for variety
        self.content_rotation = {
            "monday": ContentType.CASE_STUDY,  # Start week with strong case study
            "wednesday": ContentType.LINKEDIN_POST,  # Mid-week engagement post
            "friday": ContentType.TECHNICAL_BLOG,  # End week with technical depth
        }

        # Company targeting rotation (3-week cycle)
        self.company_rotation = [
            ["anthropic", "notion", "stripe"],  # Week 1: Top targets
            ["databricks", "openai", "cohere"],  # Week 2: ML/AI focus
            ["huggingface", "runway", "scale"],  # Week 3: Emerging companies
        ]

    async def create_weekly_schedule(
        self,
        week_start: Optional[datetime] = None,
        target_companies: Optional[List[str]] = None,
        custom_platforms: Optional[List[Platform]] = None,
    ) -> WeeklyContentPlan:
        """
        Create a new weekly content schedule.

        Args:
            week_start: Start of the week (defaults to next Monday)
            target_companies: Companies to target (defaults to rotation)
            custom_platforms: Platforms to use (defaults to all)

        Returns:
            WeeklyContentPlan with scheduled entries
        """
        if not week_start:
            week_start = self._get_next_monday()

        if not target_companies:
            week_number = self._get_week_number(week_start)
            target_companies = self.company_rotation[
                week_number % len(self.company_rotation)
            ]

        platforms = custom_platforms or [
            Platform.LINKEDIN,
            Platform.MEDIUM,
            Platform.DEVTO,
        ]

        logger.info(
            "creating_weekly_schedule",
            week_start=week_start.isoformat(),
            target_companies=target_companies,
            platforms=[p.value for p in platforms],
        )

        plan = WeeklyContentPlan(
            week_start=week_start,
            target_posts=3,
            platforms=platforms,
            target_companies=target_companies,
            content_types=list(self.content_rotation.values()),
        )

        # Get best achievements for the week
        achievements = await self._select_weekly_achievements(target_companies)

        if len(achievements) < 3:
            logger.warning(
                "insufficient_achievements", found=len(achievements), required=3
            )
            # Fallback: get any high-quality achievements
            achievements = await self._get_fallback_achievements()

        # Create scheduled entries
        schedule_entries = await self._create_schedule_entries(
            week_start, achievements, target_companies, platforms
        )

        plan.scheduled_entries = schedule_entries

        # Store the plan
        plan_id = f"week_{week_start.strftime('%Y%m%d')}"
        self.active_schedules[plan_id] = plan

        logger.info(
            "weekly_schedule_created",
            plan_id=plan_id,
            entries=len(schedule_entries),
            week_start=week_start.isoformat(),
        )

        return plan

    async def _select_weekly_achievements(
        self, target_companies: List[str]
    ) -> List[Dict[str, Any]]:
        """Select best achievements for weekly content"""
        achievements = []

        async with self.achievement_client:
            # Get recent high-impact achievements
            recent = await self.achievement_client.get_recent_highlights(
                days=30, min_impact_score=80.0, limit=10
            )

            # Get company-targeted achievements
            for company in target_companies:
                company_achievements = (
                    await self.achievement_client.get_company_targeted(
                        company_name=company, limit=5
                    )
                )
                achievements.extend([a.dict() for a in company_achievements])

            # Add recent achievements
            achievements.extend([a.dict() for a in recent])

        # Remove duplicates and sort by impact score
        seen_ids = set()
        unique_achievements = []
        for achievement in achievements:
            if achievement["id"] not in seen_ids:
                unique_achievements.append(achievement)
                seen_ids.add(achievement["id"])

        # Sort by impact score and variety
        unique_achievements.sort(key=lambda x: x.get("impact_score", 0), reverse=True)

        # Ensure variety in categories
        return self._ensure_category_variety(unique_achievements[:10])

    def _ensure_category_variety(
        self, achievements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Ensure variety in achievement categories for diverse content"""
        categories_seen = set()
        varied_achievements = []

        # First pass: one from each category
        for achievement in achievements:
            category = achievement.get("category", "general")
            if category not in categories_seen:
                varied_achievements.append(achievement)
                categories_seen.add(category)
                if len(varied_achievements) >= 5:
                    break

        # Second pass: fill remaining slots
        for achievement in achievements:
            if achievement not in varied_achievements:
                varied_achievements.append(achievement)
                if len(varied_achievements) >= 8:
                    break

        return varied_achievements

    async def _get_fallback_achievements(self) -> List[Dict[str, Any]]:
        """Get fallback achievements when target selection fails"""
        async with self.achievement_client:
            # Get any portfolio-ready achievements
            all_achievements = await self.achievement_client.list_achievements(
                portfolio_ready_only=True,
                min_impact_score=70.0,
                page_size=10,
                sort_by="impact_score",
                sort_order="desc",
            )
            return [a.dict() for a in all_achievements.achievements]

    async def _create_schedule_entries(
        self,
        week_start: datetime,
        achievements: List[Dict[str, Any]],
        target_companies: List[str],
        platforms: List[Platform],
    ) -> List[ContentScheduleEntry]:
        """Create scheduled content entries for the week"""
        entries = []

        # Standard 3-post weekly schedule
        schedule_template = [
            ("monday", Platform.LINKEDIN, ContentType.CASE_STUDY),
            ("wednesday", Platform.MEDIUM, ContentType.TECHNICAL_BLOG),
            ("friday", Platform.DEVTO, ContentType.LINKEDIN_POST),
        ]

        for i, (day, platform, content_type) in enumerate(schedule_template):
            if i >= len(achievements):
                break

            achievement = achievements[i]
            company = (
                target_companies[i % len(target_companies)]
                if target_companies
                else None
            )

            # Calculate scheduled time
            day_offset = [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ].index(day)
            scheduled_date = week_start + timedelta(days=day_offset)
            posting_time = self.posting_schedule.get(platform, {}).get(day, time(10, 0))
            scheduled_time = datetime.combine(scheduled_date.date(), posting_time)

            entry = ContentScheduleEntry(
                id=f"{week_start.strftime('%Y%m%d')}_{day}_{platform.value}",
                achievement_id=achievement["id"],
                content_type=content_type,
                platform=platform,
                target_company=company,
                scheduled_time=scheduled_time,
            )

            entries.append(entry)

        return entries

    async def generate_scheduled_content(self, entry: ContentScheduleEntry) -> bool:
        """Generate content for a scheduled entry"""
        try:
            logger.info(
                "generating_scheduled_content",
                entry_id=entry.id,
                achievement_id=entry.achievement_id,
                platform=entry.platform.value,
            )

            # Get achievement data
            async with self.achievement_client:
                achievement = await self.achievement_client.get_achievement(
                    entry.achievement_id
                )
                if not achievement:
                    logger.error(
                        "achievement_not_found", achievement_id=entry.achievement_id
                    )
                    entry.status = "failed"
                    return False

            # Create content request
            request = ProfessionalContentRequest(
                achievement_id=entry.achievement_id,
                content_type=entry.content_type,
                target_company=entry.target_company,
                platform=entry.platform,
                tone="professional",
                include_hook=True,
                include_metrics=True,
            )

            # Generate content using professional engine (with viral optimization)
            async with self.content_engine:
                result = await self.content_engine.generate_professional_content(
                    request, achievement.dict()
                )

            # Quality gate: minimum engagement and quality scores
            if result.engagement_score < 60.0 or result.quality_score < 70.0:
                logger.warning(
                    "content_quality_below_threshold",
                    entry_id=entry.id,
                    engagement_score=result.engagement_score,
                    quality_score=result.quality_score,
                )
                # Could retry with different approach or mark for manual review

            entry.generated_content = result
            entry.status = "generated"

            logger.info(
                "content_generation_successful",
                entry_id=entry.id,
                engagement_score=result.engagement_score,
                quality_score=result.quality_score,
            )

            return True

        except Exception as e:
            logger.error("content_generation_failed", entry_id=entry.id, error=str(e))
            entry.status = "failed"
            return False

    async def process_weekly_schedule(self, plan_id: str) -> Dict[str, Any]:
        """Process all entries in a weekly schedule"""
        if plan_id not in self.active_schedules:
            raise ValueError(f"Schedule {plan_id} not found")

        plan = self.active_schedules[plan_id]
        results = {"processed": 0, "successful": 0, "failed": 0, "entries": []}

        logger.info(
            "processing_weekly_schedule",
            plan_id=plan_id,
            total_entries=len(plan.scheduled_entries),
        )

        # Process entries that are due
        now = datetime.now()
        for entry in plan.scheduled_entries:
            results["processed"] += 1

            # Skip if not due yet (allow 1 hour early processing)
            if entry.scheduled_time > now + timedelta(hours=1):
                continue

            # Skip if already processed
            if entry.status in ["generated", "published"]:
                results["successful"] += 1
                continue

            # Generate content
            success = await self.generate_scheduled_content(entry)

            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1

            results["entries"].append(
                {
                    "id": entry.id,
                    "status": entry.status,
                    "platform": entry.platform.value,
                    "scheduled_time": entry.scheduled_time.isoformat(),
                    "engagement_score": entry.generated_content.engagement_score
                    if entry.generated_content
                    else None,
                }
            )

        logger.info("weekly_schedule_processed", plan_id=plan_id, results=results)

        return results

    async def get_upcoming_content(self, days: int = 7) -> List[ContentScheduleEntry]:
        """Get upcoming scheduled content entries"""
        upcoming = []
        now = datetime.now()
        cutoff = now + timedelta(days=days)

        for plan in self.active_schedules.values():
            for entry in plan.scheduled_entries:
                if now <= entry.scheduled_time <= cutoff:
                    upcoming.append(entry)

        # Sort by scheduled time
        upcoming.sort(key=lambda x: x.scheduled_time)
        return upcoming

    async def get_content_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of generated content"""
        total_generated = 0
        avg_engagement = 0.0
        avg_quality = 0.0
        platform_breakdown = {}
        company_performance = {}

        for plan in self.active_schedules.values():
            for entry in plan.scheduled_entries:
                if entry.generated_content:
                    total_generated += 1
                    avg_engagement += entry.generated_content.engagement_score
                    avg_quality += entry.generated_content.quality_score

                    # Platform breakdown
                    platform = entry.platform.value
                    if platform not in platform_breakdown:
                        platform_breakdown[platform] = {
                            "count": 0,
                            "avg_engagement": 0.0,
                        }
                    platform_breakdown[platform]["count"] += 1
                    platform_breakdown[platform]["avg_engagement"] += (
                        entry.generated_content.engagement_score
                    )

                    # Company performance
                    if entry.target_company:
                        company = entry.target_company
                        if company not in company_performance:
                            company_performance[company] = {
                                "count": 0,
                                "avg_engagement": 0.0,
                            }
                        company_performance[company]["count"] += 1
                        company_performance[company]["avg_engagement"] += (
                            entry.generated_content.engagement_score
                        )

        if total_generated > 0:
            avg_engagement /= total_generated
            avg_quality /= total_generated

            # Calculate platform averages
            for platform_data in platform_breakdown.values():
                if platform_data["count"] > 0:
                    platform_data["avg_engagement"] /= platform_data["count"]

            # Calculate company averages
            for company_data in company_performance.values():
                if company_data["count"] > 0:
                    company_data["avg_engagement"] /= company_data["count"]

        return {
            "total_generated": total_generated,
            "avg_engagement_score": avg_engagement,
            "avg_quality_score": avg_quality,
            "platform_breakdown": platform_breakdown,
            "company_performance": company_performance,
            "active_schedules": len(self.active_schedules),
        }

    def _get_next_monday(self) -> datetime:
        """Get the next Monday's date"""
        today = datetime.now().date()
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:  # Today is Monday
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)
        return datetime.combine(next_monday, time(0, 0))

    def _get_week_number(self, date: datetime) -> int:
        """Get week number of the year"""
        return date.isocalendar()[1]


# Singleton instance
_content_scheduler = None


def get_content_scheduler() -> ContentScheduler:
    """Get singleton content scheduler"""
    global _content_scheduler
    if _content_scheduler is None:
        _content_scheduler = ContentScheduler()
    return _content_scheduler
