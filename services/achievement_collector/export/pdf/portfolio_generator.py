"""
Portfolio generator - Creates comprehensive career portfolios.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from ..base import BaseExporter


class PortfolioGenerator(BaseExporter):
    """Generate comprehensive career portfolios with visualizations."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles for portfolio."""
        # Cover page title
        self.styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=self.styles["Heading1"],
                fontSize=36,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=24,
                alignment=1,  # Center
            )
        )

        # Section headers
        self.styles.add(
            ParagraphStyle(
                name="PortfolioSection",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=colors.HexColor("#34495e"),
                spaceAfter=18,
                spaceBefore=24,
            )
        )

        # Achievement details
        self.styles.add(
            ParagraphStyle(
                name="AchievementDetail",
                parent=self.styles["Normal"],
                fontSize=11,
                leftIndent=20,
                rightIndent=20,
                spaceAfter=12,
            )
        )

    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_info: Optional[Dict[str, str]] = None,
        filename: Optional[str] = None,
        include_charts: bool = True,
    ) -> str:
        """
        Generate a comprehensive portfolio PDF.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            user_info: User information
            filename: Output filename
            include_charts: Include visualization charts

        Returns:
            Path to generated PDF
        """
        achievements = self.get_achievements(db, user_id, filters)

        if not filename:
            filename = f"portfolio_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

        # Create PDF document
        doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
        )

        # Build content
        story = []

        # Cover page
        story.extend(self._create_cover_page(user_info, achievements))
        story.append(PageBreak())

        # Table of contents
        story.extend(self._create_table_of_contents())
        story.append(PageBreak())

        # Executive summary
        story.extend(self._create_executive_summary(achievements))

        # Skills overview with charts
        if include_charts:
            story.extend(self._create_skills_overview(achievements))
            story.append(PageBreak())

        # Achievement timeline
        story.extend(self._create_achievement_timeline(achievements))
        story.append(PageBreak())

        # Detailed achievements by category
        story.extend(self._create_detailed_achievements(achievements))

        # Impact analysis
        if include_charts:
            story.extend(self._create_impact_analysis(achievements))

        # Generate PDF
        doc.build(story)

        return filename

    def _create_cover_page(
        self, user_info: Optional[Dict[str, str]], achievements: List
    ) -> List:
        """Create portfolio cover page."""
        story = []

        # Add spacing
        story.append(Spacer(1, 2 * inch))

        # Title
        story.append(Paragraph("PROFESSIONAL PORTFOLIO", self.styles["CoverTitle"]))

        # User name
        if user_info and user_info.get("name"):
            story.append(Paragraph(user_info["name"], self.styles["Title"]))

        # Date range
        if achievements:
            earliest = min(a.completed_at for a in achievements if a.completed_at)
            latest = max(a.completed_at for a in achievements if a.completed_at)
            date_range = f"{earliest.strftime('%B %Y')} - {latest.strftime('%B %Y')}"
            story.append(Paragraph(date_range, self.styles["Normal"]))

        # Stats summary
        story.append(Spacer(1, 1 * inch))

        stats_data = [
            ["Total Achievements", str(len(achievements))],
            ["Total Impact Score", str(sum(a.impact_score or 0 for a in achievements))],
            [
                "Skills Demonstrated",
                str(
                    len(
                        set(
                            skill
                            for a in achievements
                            if a.skills_demonstrated
                            for skill in a.skills_demonstrated
                        )
                    )
                ),
            ],
            [
                "Total Project Hours",
                f"{sum(a.duration_hours or 0 for a in achievements):,}",
            ],
        ]

        stats_table = Table(stats_data, colWidths=[3 * inch, 2 * inch])
        stats_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )

        story.append(stats_table)

        return story

    def _create_table_of_contents(self) -> List:
        """Create table of contents."""
        story = []

        story.append(Paragraph("TABLE OF CONTENTS", self.styles["PortfolioSection"]))

        toc_items = [
            "1. Executive Summary",
            "2. Skills Overview",
            "3. Achievement Timeline",
            "4. Detailed Achievements",
            "5. Impact Analysis",
        ]

        for item in toc_items:
            story.append(Paragraph(item, self.styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        return story

    def _create_executive_summary(self, achievements: List) -> List:
        """Create executive summary section."""
        story = []

        story.append(Paragraph("1. EXECUTIVE SUMMARY", self.styles["PortfolioSection"]))

        # Career highlights
        if achievements:
            # Find highest impact achievements
            top_achievements = sorted(
                achievements, key=lambda a: a.impact_score or 0, reverse=True
            )[:3]

            summary_text = f"""
            This portfolio represents {len(achievements)} professional achievements spanning 
            {len(set(a.category for a in achievements))} different areas of expertise. 
            The cumulative impact score of {sum(a.impact_score or 0 for a in achievements)} 
            reflects consistent delivery of high-value solutions.
            """

            story.append(Paragraph(summary_text, self.styles["AchievementDetail"]))

            story.append(Paragraph("<b>Top Achievements:</b>", self.styles["Normal"]))

            for achievement in top_achievements:
                story.append(
                    Paragraph(
                        f"• {achievement.title} (Impact: {achievement.impact_score})",
                        self.styles["AchievementDetail"],
                    )
                )

        story.append(Spacer(1, 0.3 * inch))

        return story

    def _create_skills_overview(self, achievements: List) -> List:
        """Create skills overview with visualization."""
        story = []

        story.append(Paragraph("2. SKILLS OVERVIEW", self.styles["PortfolioSection"]))

        # Aggregate skills
        skill_counts = {}
        for achievement in achievements:
            if achievement.skills_demonstrated:
                for skill in achievement.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        if skill_counts:
            # Create skill chart
            chart_path = self._create_skill_chart(skill_counts)
            if chart_path and os.path.exists(chart_path):
                img = Image(chart_path, width=6 * inch, height=4 * inch)
                story.append(img)

            # Skill categories
            story.append(
                Paragraph("<b>Skill Proficiency Levels:</b>", self.styles["Normal"])
            )

            sorted_skills = sorted(
                skill_counts.items(), key=lambda x: x[1], reverse=True
            )

            skill_table_data = [["Skill", "Projects", "Level"]]
            for skill, count in sorted_skills[:15]:
                level = (
                    "Expert"
                    if count >= 5
                    else "Proficient"
                    if count >= 2
                    else "Familiar"
                )
                skill_table_data.append([skill, str(count), level])

            skill_table = Table(
                skill_table_data, colWidths=[2.5 * inch, 1 * inch, 1.5 * inch]
            )
            skill_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(skill_table)

        return story

    def _create_achievement_timeline(self, achievements: List) -> List:
        """Create achievement timeline."""
        story = []

        story.append(
            Paragraph("3. ACHIEVEMENT TIMELINE", self.styles["PortfolioSection"])
        )

        # Sort by date
        sorted_achievements = sorted(
            achievements, key=lambda a: a.completed_at or datetime.min, reverse=True
        )

        # Group by year/quarter
        current_period = None

        for achievement in sorted_achievements:
            if achievement.completed_at:
                period = f"{achievement.completed_at.year} Q{(achievement.completed_at.month - 1) // 3 + 1}"

                if period != current_period:
                    if current_period:
                        story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(f"<b>{period}</b>", self.styles["Heading3"]))
                    current_period = period

                # Achievement entry
                entry_text = f"• <b>{achievement.title}</b>"
                if achievement.category:
                    entry_text += f" [{achievement.category}]"
                if achievement.impact_score:
                    entry_text += f" - Impact: {achievement.impact_score}"

                story.append(Paragraph(entry_text, self.styles["AchievementDetail"]))

                if achievement.business_value:
                    story.append(
                        Paragraph(
                            f"  {achievement.business_value}",
                            self.styles["AchievementDetail"],
                        )
                    )

        return story

    def _create_detailed_achievements(self, achievements: List) -> List:
        """Create detailed achievements by category."""
        story = []

        story.append(
            Paragraph("4. DETAILED ACHIEVEMENTS", self.styles["PortfolioSection"])
        )

        # Group by category
        categories = {}
        for achievement in achievements:
            if achievement.category not in categories:
                categories[achievement.category] = []
            categories[achievement.category].append(achievement)

        # Create section for each category
        for category, category_achievements in sorted(categories.items()):
            story.append(
                Paragraph(
                    f"<b>{category.upper()}</b> ({len(category_achievements)} achievements)",
                    self.styles["Heading2"],
                )
            )

            # Sort by impact within category
            sorted_achievements = sorted(
                category_achievements, key=lambda a: a.impact_score or 0, reverse=True
            )

            for achievement in sorted_achievements[:5]:  # Top 5 per category
                # Achievement title
                story.append(
                    Paragraph(f"<b>{achievement.title}</b>", self.styles["Heading3"])
                )

                # Details table
                details_data = []

                if achievement.description:
                    details_data.append(["Description", achievement.description])
                if achievement.impact_score:
                    details_data.append(["Impact Score", str(achievement.impact_score)])
                if achievement.complexity_score:
                    details_data.append(
                        ["Complexity", f"{achievement.complexity_score}/100"]
                    )
                if achievement.duration_hours:
                    details_data.append(
                        ["Duration", f"{achievement.duration_hours} hours"]
                    )
                if achievement.skills_demonstrated:
                    details_data.append(
                        ["Skills", ", ".join(achievement.skills_demonstrated)]
                    )
                if achievement.business_value:
                    details_data.append(["Business Impact", achievement.business_value])

                if details_data:
                    details_table = Table(
                        details_data, colWidths=[1.5 * inch, 4.5 * inch]
                    )
                    details_table.setStyle(
                        TableStyle(
                            [
                                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                ("FONTSIZE", (0, 0), (-1, -1), 10),
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ]
                        )
                    )

                    story.append(details_table)
                    story.append(Spacer(1, 0.3 * inch))

            story.append(PageBreak())

        return story

    def _create_impact_analysis(self, achievements: List) -> List:
        """Create impact analysis section."""
        story = []

        story.append(Paragraph("5. IMPACT ANALYSIS", self.styles["PortfolioSection"]))

        # Create impact distribution chart
        chart_path = self._create_impact_chart(achievements)
        if chart_path and os.path.exists(chart_path):
            img = Image(chart_path, width=6 * inch, height=4 * inch)
            story.append(img)

        # Impact statistics
        impact_scores = [a.impact_score for a in achievements if a.impact_score]
        if impact_scores:
            stats_text = f"""
            <b>Impact Statistics:</b><br/>
            • Total Impact Score: {sum(impact_scores)}<br/>
            • Average Impact per Achievement: {sum(impact_scores) / len(impact_scores):.1f}<br/>
            • Highest Impact: {max(impact_scores)}<br/>
            • High-Impact Achievements (80+): {len([s for s in impact_scores if s >= 80])}<br/>
            """

            story.append(Paragraph(stats_text, self.styles["AchievementDetail"]))

        return story

    def _create_skill_chart(self, skill_counts: Dict[str, int]) -> str:
        """Create skill proficiency chart."""
        # Sort and take top skills
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[
            :12
        ]

        skills = [s[0] for s in sorted_skills]
        counts = [s[1] for s in sorted_skills]

        # Create horizontal bar chart
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.barh(skills, counts, color="#3498db")

        # Add value labels
        for i, (count, bar) in enumerate(zip(counts, bars)):
            ax.text(
                bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                str(count),
                ha="left",
                va="center",
            )

        ax.set_xlabel("Number of Projects")
        ax.set_title("Technical Skills Distribution")
        ax.set_xlim(0, max(counts) * 1.1)

        # Style
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Save chart
        chart_path = "temp_skill_chart.png"
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close()

        return chart_path

    def _create_impact_chart(self, achievements: List) -> str:
        """Create impact distribution chart."""
        # Group by impact ranges
        impact_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}

        for achievement in achievements:
            if achievement.impact_score:
                if achievement.impact_score <= 20:
                    impact_ranges["0-20"] += 1
                elif achievement.impact_score <= 40:
                    impact_ranges["21-40"] += 1
                elif achievement.impact_score <= 60:
                    impact_ranges["41-60"] += 1
                elif achievement.impact_score <= 80:
                    impact_ranges["61-80"] += 1
                else:
                    impact_ranges["81-100"] += 1

        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 6))

        labels = list(impact_ranges.keys())
        sizes = list(impact_ranges.values())
        colors = ["#e74c3c", "#e67e22", "#f39c12", "#2ecc71", "#27ae60"]

        # Only show non-zero segments
        non_zero = [
            (label, size, color)
            for label, size, color in zip(labels, sizes, colors)
            if size > 0
        ]
        if non_zero:
            labels, sizes, colors = zip(*non_zero)

            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90
            )

            ax.set_title("Achievement Impact Distribution")

            # Save chart
            chart_path = "temp_impact_chart.png"
            plt.tight_layout()
            plt.savefig(chart_path, dpi=150, bbox_inches="tight")
            plt.close()

            return chart_path

        return None
