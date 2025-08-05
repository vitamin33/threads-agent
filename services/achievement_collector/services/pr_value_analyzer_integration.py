"""PR Value Analyzer Integration for Achievement Collector.

This module integrates the PR value analysis system with the achievement collector,
automatically creating achievements with enriched business metrics from PR analysis.
"""

import json
import subprocess
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from services.achievement_collector.db.config import get_db
from services.achievement_collector.db.models import Achievement
from services.achievement_collector.api.schemas import AchievementCreate
from services.achievement_collector.api.routes.achievements import (
    create_achievement_sync,
)
from services.achievement_collector.core.logging import setup_logging

logger = setup_logging(__name__)


class PRValueAnalyzerIntegration:
    """Integrates PR value analysis into achievement tracking."""

    def __init__(self):
        self.analyzer_script = (
            Path(__file__).parent.parent.parent.parent
            / "scripts"
            / "pr-value-analyzer.py"
        )
        self.min_overall_score = float(os.getenv("MIN_PR_SCORE_FOR_ACHIEVEMENT", "6.0"))

    async def analyze_and_create_achievement(
        self, pr_number: str
    ) -> Optional[Achievement]:
        """Analyze PR and create achievement with enriched metrics."""
        try:
            # Run PR value analyzer
            analysis_result = await self._run_pr_analyzer(pr_number)
            if not analysis_result:
                logger.warning(f"No analysis results for PR #{pr_number}")
                return None

            # Check if PR already tracked
            db = next(get_db())
            try:
                existing = (
                    db.query(Achievement)
                    .filter_by(source_type="github_pr", source_id=f"PR-{pr_number}")
                    .first()
                )

                if existing:
                    # Update existing achievement with enriched metrics
                    return await self._update_achievement_metrics(
                        existing, analysis_result, db
                    )
                else:
                    # Create new achievement
                    return await self._create_enriched_achievement(
                        pr_number, analysis_result, db
                    )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to analyze PR #{pr_number}: {e}")
            return None

    async def _run_pr_analyzer(self, pr_number: str) -> Optional[Dict[str, Any]]:
        """Run the PR value analyzer script."""
        try:
            # Execute analyzer
            subprocess.run(
                ["python", str(self.analyzer_script), pr_number],
                capture_output=True,
                text=True,
                check=False,
            )

            # Read analysis results
            analysis_file = f"pr_{pr_number}_value_analysis.json"
            if Path(analysis_file).exists():
                with open(analysis_file, "r") as f:
                    return json.load(f)

            logger.warning(f"Analysis file not found: {analysis_file}")
            return None

        except Exception as e:
            logger.error(f"Error running PR analyzer: {e}")
            return None

    async def _create_enriched_achievement(
        self, pr_number: str, analysis: Dict[str, Any], db
    ) -> Optional[Achievement]:
        """Create achievement with enriched business metrics."""

        # Check overall score threshold
        overall_score = analysis.get("kpis", {}).get("overall_score", 0)
        if overall_score < self.min_overall_score:
            logger.info(
                f"PR #{pr_number} score {overall_score} below threshold {self.min_overall_score}"
            )
            return None

        # Extract business metrics
        business_metrics = analysis.get("business_metrics", {})
        technical_metrics = analysis.get("technical_metrics", {})
        performance_metrics = technical_metrics.get("performance", {})
        code_metrics = technical_metrics.get("code_metrics", {})

        # Build comprehensive metrics
        metrics = {
            # Business value metrics
            "throughput_improvement_percent": business_metrics.get(
                "throughput_improvement_percent", 0
            ),
            "infrastructure_savings_estimate": business_metrics.get(
                "infrastructure_savings_estimate", 0
            ),
            "user_experience_score": business_metrics.get("user_experience_score", 0),
            "roi_year_one_percent": business_metrics.get("roi_year_one_percent", 0),
            "payback_period_months": business_metrics.get("payback_period_months", 0),
            # Performance metrics
            "peak_rps": performance_metrics.get("peak_rps", 0),
            "latency_ms": performance_metrics.get("latency_ms", 0),
            "success_rate": performance_metrics.get("success_rate", 0),
            "test_coverage": performance_metrics.get("test_coverage", 0),
            # Code metrics
            "files_changed": code_metrics.get("files_changed", 0),
            "lines_added": code_metrics.get("lines_added", 0),
            "lines_deleted": code_metrics.get("lines_deleted", 0),
            "code_churn": code_metrics.get("code_churn", 0),
            # KPIs
            "performance_score": analysis.get("kpis", {}).get("performance_score", 0),
            "quality_score": analysis.get("kpis", {}).get("quality_score", 0),
            "business_value_score": analysis.get("kpis", {}).get(
                "business_value_score", 0
            ),
            "innovation_score": technical_metrics.get("innovation_score", 0),
            "overall_score": overall_score,
        }

        # Extract achievement tags
        tags = analysis.get("achievement_tags", [])
        tags.append(f"pr-{pr_number}")
        tags.append(f"score-{int(overall_score)}")

        # Determine impact level
        impact_level = self._determine_impact_level(overall_score, business_metrics)

        # Generate enriched description
        description = self._generate_enriched_description(pr_number, analysis)

        # Create achievement
        achievement_data = AchievementCreate(
            title=f"High-Impact PR #{pr_number} - {impact_level}",
            category=self._determine_category(tags),
            description=description,
            started_at=datetime.fromisoformat(analysis["timestamp"]),
            completed_at=datetime.fromisoformat(analysis["timestamp"]),
            source_type="github_pr",
            source_id=f"PR-{pr_number}",
            tags=tags[:20],  # Limit tags
            skills_demonstrated=self._extract_skills(analysis),
            metrics_before={},  # Could be enhanced with baseline metrics
            metrics_after=metrics,
            impact_score=overall_score * 10,  # Convert to 0-100 scale
            complexity_score=technical_metrics.get("innovation_score", 5) * 10,
            portfolio_ready=overall_score >= 7.0,
            metadata={
                "pr_number": pr_number,
                "value_analysis": analysis,
                "future_impact": analysis.get("future_impact", {}),
                "ai_insights": self._extract_ai_insights_from_achievement_file(
                    pr_number
                ),
            },
        )

        return create_achievement_sync(db, achievement_data)

    async def _update_achievement_metrics(
        self, achievement: Achievement, analysis: Dict[str, Any], db
    ) -> Achievement:
        """Update existing achievement with enriched metrics."""

        # Merge existing metrics with new analysis
        existing_metrics = achievement.metrics_after or {}
        business_metrics = analysis.get("business_metrics", {})

        # Update metrics
        existing_metrics.update(
            {
                "throughput_improvement_percent": business_metrics.get(
                    "throughput_improvement_percent", 0
                ),
                "infrastructure_savings_estimate": business_metrics.get(
                    "infrastructure_savings_estimate", 0
                ),
                "user_experience_score": business_metrics.get(
                    "user_experience_score", 0
                ),
                "roi_year_one_percent": business_metrics.get("roi_year_one_percent", 0),
                "payback_period_months": business_metrics.get(
                    "payback_period_months", 0
                ),
                "overall_score": analysis.get("kpis", {}).get("overall_score", 0),
            }
        )

        achievement.metrics_after = existing_metrics

        # Update metadata
        metadata = achievement.metadata or {}
        metadata["value_analysis"] = analysis
        metadata["future_impact"] = analysis.get("future_impact", {})
        metadata["ai_insights"] = self._extract_ai_insights_from_achievement_file(
            achievement.source_id.replace("PR-", "")
        )
        achievement.metadata = metadata

        # Update portfolio readiness based on score
        overall_score = analysis.get("kpis", {}).get("overall_score", 0)
        if overall_score >= 7.0:
            achievement.portfolio_ready = True

        # Add new tags
        existing_tags = achievement.tags or []
        new_tags = analysis.get("achievement_tags", [])
        achievement.tags = list(set(existing_tags + new_tags))[:20]

        db.commit()
        db.refresh(achievement)

        logger.info(f"Updated achievement {achievement.id} with enriched metrics")
        return achievement

    def _determine_impact_level(self, score: float, business_metrics: Dict) -> str:
        """Determine impact level from score and metrics."""
        if score >= 9:
            return "🌟 Exceptional Impact"
        elif score >= 8:
            return "🚀 High Impact"
        elif score >= 7:
            return "💪 Significant Impact"
        elif score >= 6:
            return "✅ Good Impact"
        else:
            return "📈 Moderate Impact"

    def _determine_category(self, tags: List[str]) -> str:
        """Determine category from tags."""
        category_mapping = {
            "high_performance_implementation": "optimization",
            "cost_optimization": "infrastructure",
            "kubernetes_deployment": "infrastructure",
            "ai_ml_feature": "feature",
            "production_ready": "deployment",
        }

        for tag in tags:
            if tag in category_mapping:
                return category_mapping[tag]

        return "development"

    def _extract_skills(self, analysis: Dict[str, Any]) -> List[str]:
        """Extract skills from analysis."""
        skills = set()

        # From achievement tags
        tag_skill_mapping = {
            "high_performance_implementation": [
                "Performance Optimization",
                "System Architecture",
            ],
            "cost_optimization": ["Cost Management", "Resource Optimization"],
            "kubernetes_deployment": [
                "Kubernetes",
                "Container Orchestration",
                "DevOps",
            ],
            "ai_ml_feature": ["Machine Learning", "AI Engineering", "Data Science"],
            "production_ready": ["Production Deployment", "Reliability Engineering"],
        }

        for tag in analysis.get("achievement_tags", []):
            if tag in tag_skill_mapping:
                skills.update(tag_skill_mapping[tag])

        # From performance metrics
        if (
            analysis.get("technical_metrics", {})
            .get("performance", {})
            .get("peak_rps", 0)
            > 500
        ):
            skills.add("High-Performance Systems")

        if (
            analysis.get("technical_metrics", {})
            .get("performance", {})
            .get("test_coverage", 0)
            > 90
        ):
            skills.add("Test-Driven Development")

        # Always include these
        skills.update(["Git", "Code Review", "Technical Leadership"])

        return list(skills)[:15]  # Limit skills

    def _generate_enriched_description(
        self, pr_number: str, analysis: Dict[str, Any]
    ) -> str:
        """Generate enriched description with business value highlights."""
        parts = []

        # Performance highlights
        perf = analysis.get("technical_metrics", {}).get("performance", {})
        if perf.get("peak_rps"):
            parts.append(f"Achieved {perf['peak_rps']} RPS peak performance")

        if perf.get("latency_ms"):
            parts.append(f"with <{perf['latency_ms']}ms latency")

        # Business value highlights
        business = analysis.get("business_metrics", {})
        if business.get("infrastructure_savings_estimate"):
            parts.append(
                f"Estimated ${business['infrastructure_savings_estimate']:,.0f} "
                "annual infrastructure savings"
            )

        if business.get("roi_year_one_percent"):
            parts.append(f"with {business['roi_year_one_percent']:.0f}% first-year ROI")

        # Code metrics
        code = analysis.get("technical_metrics", {}).get("code_metrics", {})
        if code:
            parts.append(
                f"Modified {code.get('files_changed', 0)} files with "
                f"{code.get('lines_added', 0)} additions and "
                f"{code.get('lines_deleted', 0)} deletions"
            )

        # Future impact
        future = analysis.get("future_impact", {})
        if future.get("revenue_impact_3yr"):
            parts.append(
                f"Projected 3-year revenue impact: ${future['revenue_impact_3yr']:,.0f}"
            )

        return ". ".join(parts) + "."

    def _extract_ai_insights_from_achievement_file(
        self, pr_number: str
    ) -> Optional[Dict[str, Any]]:
        """Extract AI insights from the achievement file if it exists."""
        try:
            achievement_file = Path(f".achievements/pr_{pr_number}_achievement.json")
            if achievement_file.exists():
                with open(achievement_file, "r") as f:
                    data = json.load(f)
                    return data.get("ai_insights", {})
            return {}
        except Exception as e:
            logger.warning(f"Could not extract AI insights for PR #{pr_number}: {e}")
            return {}


# Export for use in webhooks and other integrations
pr_value_integration = PRValueAnalyzerIntegration()
