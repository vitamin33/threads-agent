"""
Resume generator - Creates professional resumes from achievements.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from sqlalchemy.orm import Session

from ...services.ai_analyzer import AIAnalyzer
from ..base import BaseExporter


class ResumeGenerator(BaseExporter):
    """Generate professional resumes from achievements."""

    def __init__(self):
        self.ai_analyzer = AIAnalyzer()
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()

    def _create_custom_styles(self):
        """Create custom paragraph styles."""
        # Name/Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a1a1a"),
                spaceAfter=6,
                alignment=TA_CENTER,
            )
        )

        # Section header style
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=12,
                spaceBefore=18,
                borderColor=colors.HexColor("#2c3e50"),
                borderWidth=1,
                borderPadding=3,
            )
        )

        # Achievement title style
        self.styles.add(
            ParagraphStyle(
                name="AchievementTitle",
                parent=self.styles["Heading3"],
                fontSize=11,
                textColor=colors.HexColor("#34495e"),
                spaceAfter=3,
                leftIndent=20,
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=10,
                textColor=colors.HexColor("#4a4a4a"),
                alignment=TA_JUSTIFY,
                leftIndent=20,
                rightIndent=20,
            )
        )

    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        user_info: Optional[Dict[str, str]] = None,
        filename: Optional[str] = None,
    ) -> str:
        """
        Generate a professional resume PDF.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            user_info: User contact information
            filename: Output filename

        Returns:
            Path to generated PDF
        """
        achievements = self.get_achievements(db, user_id, filters)

        if not filename:
            filename = f"resume_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

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

        # Add header with user info
        story.extend(self._create_header(user_info))

        # Add professional summary
        story.extend(await self._create_summary(achievements))

        # Add skills section
        story.extend(self._create_skills_section(achievements))

        # Add key achievements
        story.extend(self._create_achievements_section(achievements))

        # Add metrics section
        story.extend(self._create_metrics_section(achievements))

        # Generate PDF
        doc.build(story)

        return filename

    def _create_header(self, user_info: Optional[Dict[str, str]]) -> List:
        """Create resume header with contact info."""
        story = []

        # Default info if not provided
        if not user_info:
            user_info = {
                "name": "Professional Developer",
                "email": "email@example.com",
                "location": "Remote",
            }

        # Name
        story.append(
            Paragraph(user_info.get("name", "Professional"), self.styles["CustomTitle"])
        )

        # Contact info
        contact_parts = []
        if user_info.get("email"):
            contact_parts.append(user_info["email"])
        if user_info.get("phone"):
            contact_parts.append(user_info["phone"])
        if user_info.get("location"):
            contact_parts.append(user_info["location"])
        if user_info.get("linkedin"):
            contact_parts.append(user_info["linkedin"])

        if contact_parts:
            contact_text = " • ".join(contact_parts)
            story.append(Paragraph(contact_text, self.styles["Normal"]))

        story.append(Spacer(1, 0.2 * inch))

        return story

    async def _create_summary(self, achievements: List) -> List:
        """Create AI-generated professional summary."""
        story = []

        story.append(Paragraph("PROFESSIONAL SUMMARY", self.styles["SectionHeader"]))

        if achievements:
            # Generate summary using AI
            summary = await self.ai_analyzer.generate_professional_summary(achievements)
            story.append(Paragraph(summary, self.styles["CustomBody"]))
        else:
            story.append(
                Paragraph(
                    "Experienced professional with a proven track record of delivering impactful solutions.",
                    self.styles["CustomBody"],
                )
            )

        story.append(Spacer(1, 0.2 * inch))

        return story

    def _create_skills_section(self, achievements: List) -> List:
        """Create skills section from achievements."""
        story = []

        story.append(Paragraph("TECHNICAL SKILLS", self.styles["SectionHeader"]))

        # Aggregate skills
        skill_counts = {}
        for achievement in achievements:
            if achievement.skills_demonstrated:
                for skill in achievement.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        if skill_counts:
            # Sort by frequency
            sorted_skills = sorted(
                skill_counts.items(), key=lambda x: x[1], reverse=True
            )

            # Group by proficiency level
            expert_skills = [s[0] for s in sorted_skills if s[1] >= 5]
            proficient_skills = [s[0] for s in sorted_skills if 2 <= s[1] < 5]
            familiar_skills = [s[0] for s in sorted_skills if s[1] == 1]

            skill_text = ""
            if expert_skills:
                skill_text += f"<b>Expert:</b> {', '.join(expert_skills[:8])}<br/>"
            if proficient_skills:
                skill_text += (
                    f"<b>Proficient:</b> {', '.join(proficient_skills[:8])}<br/>"
                )
            if familiar_skills:
                skill_text += f"<b>Familiar:</b> {', '.join(familiar_skills[:8])}"

            story.append(Paragraph(skill_text, self.styles["CustomBody"]))
        else:
            story.append(
                Paragraph(
                    "Various technical skills demonstrated", self.styles["CustomBody"]
                )
            )

        story.append(Spacer(1, 0.2 * inch))

        return story

    def _create_achievements_section(self, achievements: List) -> List:
        """Create key achievements section."""
        story = []

        story.append(Paragraph("KEY ACHIEVEMENTS", self.styles["SectionHeader"]))

        # Sort by impact score and take top achievements
        sorted_achievements = sorted(
            achievements, key=lambda a: a.impact_score or 0, reverse=True
        )[:8]  # Top 8 achievements

        for achievement in sorted_achievements:
            # Title
            story.append(
                Paragraph(
                    f"<b>{achievement.title}</b>", self.styles["AchievementTitle"]
                )
            )

            # Description with impact
            desc_parts = []
            if achievement.description:
                desc_parts.append(achievement.description)
            if achievement.business_value:
                desc_parts.append(f"Impact: {achievement.business_value}")

            if desc_parts:
                story.append(
                    Paragraph(" • ".join(desc_parts), self.styles["CustomBody"])
                )

            # Skills used
            if achievement.skills_demonstrated:
                skills_text = (
                    f"<i>Skills: {', '.join(achievement.skills_demonstrated[:5])}</i>"
                )
                story.append(Paragraph(skills_text, self.styles["CustomBody"]))

            story.append(Spacer(1, 0.1 * inch))

        return story

    def _create_metrics_section(self, achievements: List) -> List:
        """Create metrics and impact section."""
        story = []

        story.append(Paragraph("CAREER METRICS", self.styles["SectionHeader"]))

        # Calculate metrics
        total_impact = sum(a.impact_score or 0 for a in achievements)
        avg_complexity = (
            sum(a.complexity_score or 0 for a in achievements) / len(achievements)
            if achievements
            else 0
        )
        total_hours = sum(a.duration_hours or 0 for a in achievements)

        # Category breakdown
        category_counts = {}
        for a in achievements:
            category_counts[a.category] = category_counts.get(a.category, 0) + 1

        metrics_text = f"""
        • Total Achievements: {len(achievements)}<br/>
        • Cumulative Impact Score: {total_impact}<br/>
        • Average Project Complexity: {avg_complexity:.1f}/100<br/>
        • Total Project Hours: {total_hours:,}<br/>
        • Areas of Impact: {", ".join(category_counts.keys())}
        """

        story.append(Paragraph(metrics_text, self.styles["CustomBody"]))

        return story
