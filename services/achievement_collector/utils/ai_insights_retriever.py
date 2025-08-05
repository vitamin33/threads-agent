"""AI Insights Retriever for Achievement Data

This module provides utilities to retrieve and use AI-generated insights
from stored achievements for articles, presentations, and portfolio building.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from services.achievement_collector.db.models import Achievement
from services.achievement_collector.core.logging import setup_logging

logger = setup_logging(__name__)


class AIInsightsRetriever:
    """Retrieve and format AI insights from achievements."""

    def get_achievement_insights(self, db: Session, pr_number: str) -> Optional[Dict]:
        """Get all AI insights for a specific PR achievement."""
        achievement = (
            db.query(Achievement)
            .filter_by(source_type="github_pr", source_id=f"PR-{pr_number}")
            .first()
        )

        if not achievement or not achievement.metadata_json:
            return None

        return achievement.metadata_json.get("ai_insights", {})

    def get_interview_talking_points(self, db: Session, pr_number: str) -> List[str]:
        """Get interview-ready talking points for a PR."""
        insights = self.get_achievement_insights(db, pr_number)
        if not insights:
            return []

        return insights.get("interview_talking_points", [])

    def get_article_suggestions(
        self, db: Session, pr_number: str
    ) -> Dict[str, List[str]]:
        """Get article suggestions categorized by type."""
        insights = self.get_achievement_insights(db, pr_number)
        if not insights:
            return {}

        return insights.get("article_suggestions", {})

    def get_portfolio_summary(self, db: Session, pr_number: str) -> str:
        """Get portfolio-ready summary for a PR."""
        insights = self.get_achievement_insights(db, pr_number)
        if not insights:
            return ""

        return insights.get("portfolio_summary", "")

    def get_all_article_ideas(
        self, db: Session, min_score: float = 7.0
    ) -> Dict[str, List[str]]:
        """Get all article ideas from high-impact achievements."""
        all_ideas = {
            "technical_deep_dives": [],
            "business_case_studies": [],
            "best_practices": [],
            "lessons_learned": [],
        }

        # Query high-impact achievements
        achievements = (
            db.query(Achievement)
            .filter(
                Achievement.source_type == "github_pr",
                Achievement.impact_score >= min_score * 10,  # Convert to 0-100 scale
            )
            .all()
        )

        for achievement in achievements:
            if achievement.metadata_json and "ai_insights" in achievement.metadata_json:
                suggestions = achievement.metadata_json["ai_insights"].get(
                    "article_suggestions", {}
                )

                for category, ideas in suggestions.items():
                    if category in all_ideas:
                        all_ideas[category].extend(ideas)

        # Remove duplicates
        for category in all_ideas:
            all_ideas[category] = list(set(all_ideas[category]))

        return all_ideas

    def generate_blog_post_outline(self, db: Session, pr_number: str) -> str:
        """Generate a blog post outline using stored insights."""
        achievement = (
            db.query(Achievement)
            .filter_by(source_type="github_pr", source_id=f"PR-{pr_number}")
            .first()
        )

        if not achievement:
            return ""

        insights = achievement.metadata_json.get("ai_insights", {})
        metrics = achievement.metrics_after or {}

        outline = f"""# {achievement.title}

## Introduction
{achievement.description}

## Key Achievements
"""

        # Add talking points
        for point in insights.get("interview_talking_points", [])[:3]:
            outline += f"- {point}\n"

        outline += f"""
## Technical Deep Dive

### Performance Metrics
- **Throughput**: {metrics.get("peak_rps", "N/A")} RPS
- **Latency**: {metrics.get("latency_ms", "N/A")}ms
- **Test Coverage**: {metrics.get("test_coverage", "N/A")}%

### Implementation Details
{insights.get("score_explanations", {}).get("innovation", "")}

## Business Impact
- **ROI**: {metrics.get("roi_year_one_percent", "N/A")}%
- **Cost Savings**: ${metrics.get("infrastructure_savings_estimate", 0):,}
- **Productivity Gains**: {metrics.get("productivity_hours_saved", 0)} hours/year

## Lessons Learned
{insights.get("score_explanations", {}).get("quality", "")}

## Conclusion
This project demonstrates {", ".join(achievement.skills_demonstrated[:3])} skills 
and delivers significant value through {insights.get("score_explanations", {}).get("business", "")}.

## Next Steps
Consider these related topics for future exploration:
"""

        # Add article suggestions
        suggestions = insights.get("article_suggestions", {})
        for idea in suggestions.get("technical_deep_dives", [])[:2]:
            outline += f"- {idea}\n"

        return outline


# Example usage
def demonstrate_insights_usage():
    """Show how to use stored AI insights."""
    from services.achievement_collector.db.config import get_db

    db = next(get_db())
    retriever = AIInsightsRetriever()

    # Get insights for PR #91
    insights = retriever.get_achievement_insights(db, "91")
    if insights:
        print("📊 AI Insights for PR #91:")
        print("\n🎯 Interview Talking Points:")
        for point in retriever.get_interview_talking_points(db, "91"):
            print(f"  • {point}")

        print("\n📝 Article Ideas:")
        ideas = retriever.get_article_suggestions(db, "91")
        for category, suggestions in ideas.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for idea in suggestions[:2]:
                print(f"  • {idea}")

        print("\n💼 Portfolio Summary:")
        print(retriever.get_portfolio_summary(db, "91"))

        print("\n📄 Blog Post Outline:")
        print(retriever.generate_blog_post_outline(db, "91"))

    db.close()


if __name__ == "__main__":
    demonstrate_insights_usage()
