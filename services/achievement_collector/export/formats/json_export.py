"""
JSON export functionality for achievements.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..base import BaseExporter


class JSONExporter(BaseExporter):
    """Export achievements as JSON with rich metadata."""

    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        include_analytics: bool = True,
    ) -> Dict[str, Any]:
        """
        Export achievements as structured JSON.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            include_analytics: Include analytics data

        Returns:
            JSON-serializable dictionary
        """
        achievements = self.get_achievements(db, user_id, filters)

        # Build export data
        export_data = {
            "export_metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "total_achievements": len(achievements),
                "filters_applied": filters or {},
                "format_version": "1.0",
            },
            "achievements": [self._serialize_achievement(a) for a in achievements],
        }

        # Add analytics if requested
        if include_analytics and achievements:
            export_data["analytics"] = await self._generate_analytics(achievements)

        return export_data

    def _serialize_achievement(self, achievement) -> Dict[str, Any]:
        """Serialize single achievement to JSON-compatible format."""
        return {
            "id": achievement.id,
            "title": achievement.title,
            "description": achievement.description,
            "category": achievement.category,
            "impact_score": achievement.impact_score,
            "complexity_score": achievement.complexity_score,
            "skills_demonstrated": achievement.skills_demonstrated or [],
            "tags": achievement.tags or [],
            "business_value": achievement.business_value,
            "duration_hours": achievement.duration_hours,
            "completed_at": achievement.completed_at.isoformat()
            if achievement.completed_at
            else None,
            "started_at": achievement.started_at.isoformat()
            if achievement.started_at
            else None,
            "portfolio_ready": achievement.portfolio_ready,
            "source_type": achievement.source_type,
            "source_id": achievement.source_id,
            "source_url": achievement.source_url,
            "time_saved_hours": achievement.time_saved_hours,
            "performance_improvement_pct": achievement.performance_improvement_pct,
            "evidence": achievement.evidence or {},
            "metrics_before": achievement.metrics_before or {},
            "metrics_after": achievement.metrics_after or {},
            "ai_summary": achievement.ai_summary,
            "ai_impact_analysis": achievement.ai_impact_analysis,
            "ai_technical_analysis": achievement.ai_technical_analysis,
            "portfolio_section": achievement.portfolio_section,
            "display_priority": achievement.display_priority,
        }

    async def _generate_analytics(self, achievements: List) -> Dict[str, Any]:
        """Generate analytics summary for achievements."""
        total_impact = sum(a.impact_score or 0 for a in achievements)
        avg_complexity = sum(a.complexity_score or 0 for a in achievements) / len(
            achievements
        )

        # Skill frequency analysis
        skill_counts = {}
        for achievement in achievements:
            if achievement.skills_demonstrated:
                for skill in achievement.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Category distribution
        category_counts = {}
        for achievement in achievements:
            category_counts[achievement.category] = (
                category_counts.get(achievement.category, 0) + 1
            )

        return {
            "summary": {
                "total_achievements": len(achievements),
                "total_impact_score": total_impact,
                "average_complexity": round(avg_complexity, 2),
                "total_hours": sum(a.duration_hours or 0 for a in achievements),
                "unique_skills": len(skill_counts),
                "categories": len(category_counts),
            },
            "top_skills": sorted(
                skill_counts.items(), key=lambda x: x[1], reverse=True
            )[:10],
            "category_distribution": category_counts,
            "timeline": {
                "earliest": min(
                    a.completed_at for a in achievements if a.completed_at
                ).isoformat(),
                "latest": max(
                    a.completed_at for a in achievements if a.completed_at
                ).isoformat(),
            },
        }

    def export_to_file(
        self, data: Dict[str, Any], filename: str, pretty: bool = True
    ) -> str:
        """
        Export JSON data to file.

        Args:
            data: Export data
            filename: Output filename
            pretty: Pretty-print JSON

        Returns:
            Path to exported file
        """
        with open(filename, "w") as f:
            if pretty:
                json.dump(data, f, indent=2, sort_keys=True)
            else:
                json.dump(data, f)

        return filename
