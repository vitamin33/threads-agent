"""Database operations for achievement storage."""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from ..db.models import Achievement, Base
from ..db.config import engine
from ..api.schemas import AchievementCreate
from ..core.logging import setup_logging

logger = setup_logging(__name__)

# Initialize database tables
Base.metadata.create_all(bind=engine)


def create_achievement_from_pr(
    db: Session, pr_data: Dict, analysis: Dict
) -> Achievement:
    """Create achievement record from PR analysis."""

    # Determine category from analysis
    category = _determine_category(analysis)

    # Extract metadata - handle both direct pr_data and nested metadata
    if "metadata" in pr_data:
        pr_metadata = pr_data["metadata"]
    else:
        # If pr_data is the metadata itself
        pr_metadata = pr_data

    # Calculate duration
    started_at = datetime.fromisoformat(
        pr_metadata.get("created_at", "").replace("Z", "+00:00")
    )
    completed_at = datetime.fromisoformat(
        pr_metadata.get("merged_at", "").replace("Z", "+00:00")
    )
    duration_hours = (completed_at - started_at).total_seconds() / 3600

    # Create achievement
    achievement_data = AchievementCreate(
        title=f"PR #{pr_metadata.get('pr_number', pr_metadata.get('number', ''))}: {pr_metadata.get('title', '')}",
        description=pr_metadata.get("description", pr_metadata.get("body", ""))[
            :1000
        ],  # Limit description length
        category=category,
        started_at=started_at,
        completed_at=completed_at,
        source_type="github_pr",
        source_id=f"PR-{pr_metadata.get('pr_number', pr_metadata.get('number', ''))}",
        source_url=pr_metadata.get("pr_url", pr_metadata.get("html_url", "")),
        tags=_extract_tags(analysis),
        skills_demonstrated=_extract_skills(analysis),
        evidence=analysis.get("evidence", {}),
        metrics_before={},  # Could be populated from base branch analysis
        metrics_after={
            **analysis.get("performance_metrics", {}),
            **analysis.get("business_metrics", {}),
            **analysis.get("quality_metrics", {}),
        },
        impact_score=analysis.get("composite_scores", {}).get("overall_impact", 50),
        complexity_score=analysis.get("composite_scores", {}).get(
            "technical_excellence", 50
        ),
        business_value=_extract_business_value(analysis),
        time_saved_hours=_calculate_time_saved(analysis),
        portfolio_ready=analysis.get("composite_scores", {}).get("overall_impact", 0)
        >= 70,
    )

    # Create achievement
    achievement = Achievement(**achievement_data.model_dump(exclude={"metadata"}))
    achievement.duration_hours = duration_hours

    # Add additional fields not in schema
    achievement.ai_summary = analysis.get("ai_insights", {}).get("summary")
    achievement.ai_impact_analysis = str(
        analysis.get("ai_insights", {}).get("impact_analysis", [])
    )
    achievement.ai_technical_analysis = str(
        analysis.get("ai_insights", {}).get("technical_analysis", [])
    )

    # Store the full analysis in metadata_json
    achievement.metadata_json = {
        "full_analysis": analysis,
        "stories": pr_data.get("stories", {}),
        "platform_content": pr_data.get("platform_content", {}),
    }

    db.add(achievement)
    db.commit()
    db.refresh(achievement)

    logger.info(
        f"Created achievement {achievement.id} for PR #{pr_metadata.get('pr_number', pr_metadata.get('number', 'unknown'))}"
    )

    return achievement


def update_achievement_with_stories(
    db: Session, achievement_id: int, stories: Dict
) -> Achievement:
    """Update achievement with generated stories."""

    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()

    if not achievement:
        raise ValueError(f"Achievement {achievement_id} not found")

    # Update metadata with stories
    if not achievement.metadata_json:
        achievement.metadata_json = {}

    achievement.metadata_json["stories"] = stories

    # Update AI summaries from stories
    if "technical" in stories:
        achievement.ai_technical_analysis = stories["technical"].get("full_story", "")

    if "business" in stories:
        achievement.ai_impact_analysis = stories["business"].get("full_story", "")

    if "leadership" in stories:
        achievement.ai_summary = stories["leadership"].get("summary", "")

    achievement.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(achievement)

    return achievement


def update_achievement_with_platform_content(
    db: Session, achievement_id: int, platform_content: Dict
) -> Achievement:
    """Update achievement with prepared platform content."""

    achievement = db.query(Achievement).filter(Achievement.id == achievement_id).first()

    if not achievement:
        raise ValueError(f"Achievement {achievement_id} not found")

    # Update metadata
    if not achievement.metadata_json:
        achievement.metadata_json = {}

    achievement.metadata_json["platform_content"] = platform_content
    achievement.metadata_json["platforms_ready"] = list(platform_content.keys())

    # Mark as portfolio ready if content is prepared
    if len(platform_content) >= 3:  # At least 3 platforms ready
        achievement.portfolio_ready = True

    achievement.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(achievement)

    return achievement


def get_achievement_by_pr(db: Session, pr_number: int) -> Optional[Achievement]:
    """Get achievement by PR number."""

    return (
        db.query(Achievement)
        .filter(
            Achievement.source_type == "github_pr",
            Achievement.source_id == f"PR-{pr_number}",
        )
        .first()
    )


def get_recent_achievements(
    db: Session, limit: int = 10, portfolio_ready_only: bool = False
) -> List[Achievement]:
    """Get recent achievements."""

    query = db.query(Achievement)

    if portfolio_ready_only:
        query = query.filter(Achievement.portfolio_ready.is_(True))

    return query.order_by(Achievement.created_at.desc()).limit(limit).all()


def get_achievements_for_posting(
    db: Session, platform: str, limit: int = 5
) -> List[Achievement]:
    """Get achievements ready for posting to a specific platform."""

    # Query achievements that:
    # 1. Are portfolio ready
    # 2. Have platform content prepared
    # 3. Haven't been posted to this platform yet

    achievements = (
        db.query(Achievement)
        .filter(
            Achievement.portfolio_ready.is_(True),
            Achievement.metadata_json["platforms_ready"].contains([platform]),
            # Check posting metadata - this would need more sophisticated querying
        )
        .order_by(Achievement.impact_score.desc())
        .limit(limit)
        .all()
    )

    return achievements


# Helper functions


def _determine_category(analysis: Dict) -> str:
    """Determine achievement category from analysis."""

    # Check code metrics for primary change type
    code_metrics = analysis.get("code_metrics", {})
    change_categories = code_metrics.get("change_categories", {})

    # Find category with most changes
    if change_categories:
        primary_category = max(change_categories, key=change_categories.get)

        # Map to our categories
        category_map = {
            "feature": "feature",
            "bugfix": "bugfix",
            "refactor": "refactoring",
            "test": "testing",
            "docs": "documentation",
            "config": "infrastructure",
            "dependency": "infrastructure",
        }

        return category_map.get(primary_category, "development")

    # Fallback: check if performance improvements
    if analysis.get("performance_metrics", {}).get("latency_changes"):
        return "performance"

    # Fallback: check if architectural changes
    if analysis.get("architectural_metrics", {}).get("patterns_implemented"):
        return "architecture"

    return "development"


def _extract_tags(analysis: Dict) -> List[str]:
    """Extract tags from analysis."""

    tags = []

    # Add language tags
    languages = analysis.get("code_metrics", {}).get("languages", {})
    tags.extend([lang.lower() for lang in languages.keys()][:5])

    # Add impact tags
    if analysis.get("performance_metrics"):
        tags.append("performance")

    if analysis.get("business_metrics", {}).get("financial_impact"):
        tags.append("business-impact")

    if analysis.get("security_metrics", {}).get("vulnerabilities_fixed"):
        tags.append("security")

    if analysis.get("innovation_metrics", {}).get("technical_innovation"):
        tags.append("innovation")

    # Add from PR metadata
    pr_tags = analysis.get("metadata", {}).get("labels", [])
    tags.extend([tag.lower() for tag in pr_tags][:3])

    return list(set(tags))[:15]  # Unique tags, max 15


def _extract_skills(analysis: Dict) -> List[str]:
    """Extract skills demonstrated from analysis."""

    skills = []

    # Technical skills from languages
    languages = analysis.get("code_metrics", {}).get("languages", {})
    skills.extend(list(languages.keys())[:5])

    # Skills from code quality
    test_coverage_delta = (
        analysis.get("quality_metrics", {}).get("test_coverage", {}).get("delta", 0)
        or 0
    )
    if test_coverage_delta > 5:
        skills.append("Test-Driven Development")

    if (
        analysis.get("code_metrics", {})
        .get("refactoring_metrics", {})
        .get("patterns_implemented")
    ):
        skills.append("Design Patterns")

    # Skills from architecture
    if analysis.get("architectural_metrics", {}).get("api_changes"):
        skills.append("API Design")

    if analysis.get("architectural_metrics", {}).get("database_changes"):
        skills.append("Database Design")

    # Skills from process
    reviewers_count = (
        analysis.get("team_metrics", {})
        .get("collaboration", {})
        .get("reviewers_count", 0)
        or 0
    )
    if reviewers_count > 2:
        skills.append("Team Collaboration")

    teaching_moments = (
        analysis.get("team_metrics", {})
        .get("mentorship", {})
        .get("teaching_moments", 0)
        or 0
    )
    if teaching_moments > 0:
        skills.append("Mentorship")

    # Performance skills
    if analysis.get("performance_metrics", {}).get("latency_changes"):
        skills.append("Performance Optimization")

    # Business skills
    if analysis.get("business_metrics", {}).get("financial_impact"):
        skills.append("Business Acumen")

    # General skills
    skills.extend(["Problem Solving", "Software Engineering"])

    return list(set(skills))[:15]  # Unique skills, max 15


def _extract_business_value(analysis: Dict) -> Optional[str]:
    """Extract business value statement from analysis."""

    financial = analysis.get("business_metrics", {}).get("financial_impact", {})

    values = []

    if financial.get("cost_savings"):
        values.append(f"${financial['cost_savings']:,.0f} annual cost savings")

    if financial.get("revenue_impact"):
        values.append(f"${financial['revenue_impact']:,.0f} revenue impact")

    if financial.get("efficiency_gains"):
        values.append(f"{financial['efficiency_gains']}% efficiency improvement")

    user = analysis.get("business_metrics", {}).get("user_impact", {})

    if user.get("users_affected"):
        values.append(f"{user['users_affected']:,} users benefited")

    if values:
        return " | ".join(values[:2])  # Max 2 values

    return None


def _calculate_time_saved(analysis: Dict) -> float:
    """Calculate time saved in hours from analysis."""

    operational = analysis.get("business_metrics", {}).get("operational_impact", {})

    time_saved = 0.0

    if operational.get("automation_hours_saved"):
        time_saved += operational["automation_hours_saved"]

    # Calculate from performance improvements
    perf = analysis.get("performance_metrics", {})
    if perf.get("latency_changes", {}).get("reported"):
        # Rough estimate: 1ms saved = 0.1 hour saved per month for users
        latency_saved = perf["latency_changes"]["reported"].get("before", 0) - perf[
            "latency_changes"
        ]["reported"].get("after", 0)
        if latency_saved > 0:
            time_saved += latency_saved * 0.1

    return time_saved
