# Portfolio Generator Service

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Union

import markdown
from jinja2 import Environment, FileSystemLoader

from services.achievement_collector.core.logging import setup_logging
from services.achievement_collector.db.models import Achievement

logger = setup_logging(__name__)


class PortfolioGenerator:
    """Generate portfolio documents in multiple formats"""

    def __init__(self, output_dir: str = "/tmp/portfolios"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Setup Jinja2 templates
        template_dir = os.path.join(os.path.dirname(__file__), "../templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))

    async def generate(
        self,
        achievements: List[Achievement],
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """Generate portfolio in specified format"""

        start_time = datetime.utcnow()

        # Generate version
        version = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Generate content based on format
        content: Union[str, bytes]
        if format == "markdown":
            content = await self._generate_markdown(achievements)
        elif format == "html":
            content = await self._generate_html(achievements)
        elif format == "json":
            content = await self._generate_json(achievements)
        elif format == "pdf":
            content = await self._generate_pdf(achievements)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Save to file
        filename = f"portfolio_{version}.{self._get_extension(format)}"
        file_path = os.path.join(self.output_dir, filename)

        if format == "pdf":
            # PDF is binary
            with open(file_path, "wb") as f:
                f.write(content)  # type: ignore[arg-type]
        else:
            # Text formats
            with open(file_path, "w") as f:
                f.write(content)  # type: ignore[arg-type]

        # Calculate generation time
        generation_time = (datetime.utcnow() - start_time).total_seconds()

        return {
            "version": version,
            "content": content if format != "pdf" else "[PDF Binary Content]",
            "file_path": file_path,
            "generation_time": generation_time,
        }

    def _get_extension(self, format: str) -> str:
        """Get file extension for format"""
        return {
            "markdown": "md",
            "html": "html",
            "json": "json",
            "pdf": "pdf",
        }.get(format, "txt")

    async def _generate_markdown(self, achievements: List[Achievement]) -> str:
        """Generate Markdown portfolio"""

        # Group by category
        by_category = self._group_by_category(achievements)

        # Calculate stats
        stats = self._calculate_stats(achievements)

        # Build markdown
        md_lines = [
            "# Professional Achievement Portfolio",
            "",
            f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
            "",
            "## Executive Summary",
            "",
            f"- **Total Achievements**: {stats['total']}",
            f"- **Total Value Generated**: ${stats['total_value']:,.2f}",
            f"- **Total Time Saved**: {stats['total_time_saved']:,.0f} hours/month",
            f"- **Average Impact Score**: {stats['avg_impact']:.1f}/100",
            "",
            "## Key Achievements by Category",
            "",
        ]

        for category, items in by_category.items():
            md_lines.append(f"### {category.title()}")
            md_lines.append("")

            for achievement in sorted(
                items, key=lambda x: x.impact_score or 0.0, reverse=True
            ):
                md_lines.extend(
                    [
                        f"#### {achievement.title}",
                        "",
                        f"*{achievement.ai_summary or achievement.description}*",
                        "",
                        f"- **Impact Score**: {achievement.impact_score:.0f}/100",
                        f"- **Business Value**: ${achievement.business_value:,.2f}",
                        f"- **Time Saved**: {achievement.time_saved_hours:.0f} hours/month",
                        f"- **Duration**: {achievement.duration_hours:.1f} hours",
                        f"- **Date**: {achievement.completed_at.strftime('%B %Y') if achievement.completed_at else 'N/A'}",
                        "",
                    ]
                )

                if achievement.skills_demonstrated:
                    md_lines.append(
                        f"**Skills**: {', '.join(achievement.skills_demonstrated)}"
                    )
                    md_lines.append("")

                if achievement.ai_impact_analysis:
                    md_lines.extend(
                        [
                            "**Impact Analysis**:",
                            "",
                            achievement.ai_impact_analysis,
                            "",
                        ]
                    )

        return "\n".join(md_lines)

    async def _generate_html(self, achievements: List[Achievement]) -> str:
        """Generate HTML portfolio"""

        # Convert markdown to HTML first
        md_content = await self._generate_markdown(achievements)
        html_body = markdown.markdown(md_content, extensions=["extra", "codehilite"])

        # Wrap in full HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Professional Achievement Portfolio</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                    color: #333;
                }
                h1, h2, h3, h4 {
                    color: #2c3e50;
                }
                h1 {
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }
                h2 {
                    margin-top: 40px;
                    border-bottom: 1px solid #ecf0f1;
                    padding-bottom: 5px;
                }
                code {
                    background: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                blockquote {
                    border-left: 4px solid #3498db;
                    margin: 0;
                    padding-left: 15px;
                    color: #555;
                }
            </style>
        </head>
        <body>
            {body}
        </body>
        </html>
        """

        return html_template.format(body=html_body)

    async def _generate_json(self, achievements: List[Achievement]) -> str:
        """Generate JSON portfolio"""

        data = {
            "portfolio": {
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0",
                "stats": self._calculate_stats(achievements),
                "achievements": [
                    {
                        "id": a.id,
                        "title": a.title,
                        "description": a.description,
                        "category": a.category,
                        "impact_score": a.impact_score,
                        "complexity_score": a.complexity_score,
                        "business_value": float(a.business_value)
                        if a.business_value
                        else 0.0,
                        "time_saved_hours": a.time_saved_hours,
                        "duration_hours": a.duration_hours,
                        "started_at": a.started_at.isoformat()
                        if a.started_at
                        else None,
                        "completed_at": a.completed_at.isoformat()
                        if a.completed_at
                        else None,
                        "tags": a.tags,
                        "skills": a.skills_demonstrated,
                        "summary": a.ai_summary,
                        "impact_analysis": a.ai_impact_analysis,
                        "technical_analysis": a.ai_technical_analysis,
                        "evidence": a.evidence,
                        "metrics": {
                            "before": a.metrics_before,
                            "after": a.metrics_after,
                        },
                    }
                    for a in achievements
                ],
            }
        }

        return json.dumps(data, indent=2, default=str)

    async def _generate_pdf(self, achievements: List[Achievement]) -> bytes:
        """Generate PDF portfolio"""

        # For now, return a placeholder
        # TODO: Implement proper PDF generation with reportlab

        return b"PDF generation not yet implemented"

    def _group_by_category(
        self, achievements: List[Achievement]
    ) -> Dict[str, List[Achievement]]:
        """Group achievements by category"""

        grouped: Dict[str, List[Achievement]] = {}
        for achievement in achievements:
            category = achievement.category or "uncategorized"
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(achievement)

        return grouped

    def _calculate_stats(self, achievements: List[Achievement]) -> Dict[str, Any]:
        """Calculate portfolio statistics"""

        if not achievements:
            return {
                "total": 0,
                "total_value": 0,
                "total_time_saved": 0,
                "avg_impact": 0,
                "avg_complexity": 0,
            }

        return {
            "total": len(achievements),
            "total_value": sum(
                float(a.business_value) if a.business_value else 0.0
                for a in achievements
            ),
            "total_time_saved": sum(a.time_saved_hours or 0.0 for a in achievements),
            "avg_impact": sum(a.impact_score or 0.0 for a in achievements)
            / len(achievements),
            "avg_complexity": sum(a.complexity_score or 0.0 for a in achievements)
            / len(achievements),
            "by_category": {
                cat: len(items)
                for cat, items in self._group_by_category(achievements).items()
            },
        }
