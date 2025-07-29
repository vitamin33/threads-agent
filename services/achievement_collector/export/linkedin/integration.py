"""
LinkedIn integration for sharing achievements.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...services.ai_analyzer import AIAnalyzer
from ..base import BaseExporter


class LinkedInPost(BaseModel):
    """LinkedIn post model."""

    title: str
    content: str
    hashtags: List[str] = Field(default_factory=list)
    achievement_id: Optional[int] = None
    post_type: str = "achievement"  # achievement, milestone, summary


class LinkedInIntegration(BaseExporter):
    """
    LinkedIn integration for sharing achievements.

    Note: Actual LinkedIn API integration requires OAuth setup.
    This implementation provides the content generation and structure.
    """

    def __init__(self):
        self.ai_analyzer = AIAnalyzer()

    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        post_type: str = "achievement",
    ) -> List[LinkedInPost]:
        """
        Generate LinkedIn posts from achievements.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters
            post_type: Type of post to generate

        Returns:
            List of LinkedIn posts ready to share
        """
        achievements = self.get_achievements(db, user_id, filters)

        if post_type == "achievement":
            return await self._generate_achievement_posts(achievements)
        elif post_type == "milestone":
            return await self._generate_milestone_post(achievements)
        elif post_type == "summary":
            return await self._generate_summary_post(achievements)
        else:
            return []

    async def _generate_achievement_posts(
        self, achievements: List
    ) -> List[LinkedInPost]:
        """Generate individual achievement posts."""
        posts = []

        # Select top achievements for posting
        top_achievements = sorted(
            achievements, key=lambda a: a.impact_score or 0, reverse=True
        )[:5]  # Top 5 achievements

        for achievement in top_achievements:
            if achievement.portfolio_ready:
                post = await self._create_achievement_post(achievement)
                posts.append(post)

        return posts

    async def _create_achievement_post(self, achievement) -> LinkedInPost:
        """Create a LinkedIn post for a single achievement."""
        # Generate engaging content using AI
        content = await self.ai_analyzer.generate_linkedin_content(achievement)

        # Generate hashtags
        hashtags = self._generate_hashtags(achievement)

        # Create post title
        title = f"🎯 {achievement.title}"

        return LinkedInPost(
            title=title,
            content=content,
            hashtags=hashtags,
            achievement_id=achievement.id,
            post_type="achievement",
        )

    async def _generate_milestone_post(self, achievements: List) -> List[LinkedInPost]:
        """Generate milestone celebration post."""
        if len(achievements) < 10:
            return []

        # Check for significant milestones
        total_impact = sum(a.impact_score or 0 for a in achievements)
        skill_count = len(
            set(
                skill
                for a in achievements
                if a.skills_demonstrated
                for skill in a.skills_demonstrated
            )
        )

        content = f"""
🎉 Celebrating a Career Milestone! 🎉

I'm thrilled to share that I've reached {len(achievements)} documented professional achievements!

📊 Key Highlights:
• Total Impact Score: {total_impact}
• Skills Mastered: {skill_count}
• Areas of Expertise: {len(set(a.category for a in achievements))}

This journey has been incredible, filled with challenges overcome and lessons learned. 
Each achievement represents not just a completed project, but growth in technical expertise 
and problem-solving capabilities.

Thank you to all the amazing teams and mentors who've been part of this journey!

What milestone are you working towards? I'd love to hear about your professional journey!
"""

        hashtags = [
            "CareerMilestone",
            "ProfessionalGrowth",
            "ContinuousLearning",
            "TechCareer",
            "Achievement",
            "SuccessStory",
        ]

        return [
            LinkedInPost(
                title="🎉 Career Milestone Achieved!",
                content=content.strip(),
                hashtags=hashtags,
                post_type="milestone",
            )
        ]

    async def _generate_summary_post(self, achievements: List) -> List[LinkedInPost]:
        """Generate quarterly/yearly summary post."""
        if not achievements:
            return []

        # Get time range
        earliest = min(a.completed_at for a in achievements if a.completed_at)
        latest = max(a.completed_at for a in achievements if a.completed_at)

        # Top achievements
        top_achievements = sorted(
            achievements, key=lambda a: a.impact_score or 0, reverse=True
        )[:3]

        # Skills growth
        all_skills = set(
            skill
            for a in achievements
            if a.skills_demonstrated
            for skill in a.skills_demonstrated
        )

        content = f"""
📈 Professional Summary: {earliest.strftime("%B %Y")} - {latest.strftime("%B %Y")}

Reflecting on an incredible period of growth and achievement:

🏆 Top Accomplishments:
{chr(10).join(f"• {a.title}" for a in top_achievements)}

💡 Skills Developed:
• Expanded expertise across {len(all_skills)} technologies
• Delivered {len(achievements)} impactful projects
• Achieved cumulative impact score of {sum(a.impact_score or 0 for a in achievements)}

🎯 Key Learning:
Every challenge is an opportunity to grow. The most complex projects often yield the most valuable insights.

Looking forward to continuing this journey of innovation and impact!

What has been your biggest professional win recently?
"""

        hashtags = [
            "ProfessionalDevelopment",
            "CareerGrowth",
            "YearInReview",
            "TechInnovation",
            "ContinuousImprovement",
        ]

        return [
            LinkedInPost(
                title="📈 Professional Growth Summary",
                content=content.strip(),
                hashtags=hashtags,
                post_type="summary",
            )
        ]

    def _generate_hashtags(self, achievement) -> List[str]:
        """Generate relevant hashtags for an achievement."""
        hashtags = []

        # Category-based hashtags
        category_tags = {
            "optimization": ["PerformanceOptimization", "Efficiency"],
            "feature": ["FeatureDevelopment", "Innovation"],
            "bugfix": ["ProblemSolving", "QualityAssurance"],
            "infrastructure": ["DevOps", "Infrastructure"],
            "refactoring": ["CodeQuality", "TechnicalDebt"],
            "documentation": ["Documentation", "KnowledgeSharing"],
            "automation": ["Automation", "Productivity"],
            "architecture": ["SoftwareArchitecture", "SystemDesign"],
        }

        if achievement.category in category_tags:
            hashtags.extend(category_tags[achievement.category])

        # Skill-based hashtags
        if achievement.skills_demonstrated:
            # Add top skills as hashtags
            for skill in achievement.skills_demonstrated[:3]:
                hashtags.append(skill.replace(" ", "").replace("-", ""))

        # Impact-based hashtags
        if achievement.impact_score and achievement.impact_score >= 80:
            hashtags.extend(["HighImpact", "Success"])

        # Default hashtags
        hashtags.extend(["Tech", "Career", "Achievement"])

        # Deduplicate and limit
        return list(dict.fromkeys(hashtags))[:10]

    def generate_recommendation_text(
        self, achievements: List, recommender_context: Optional[str] = None
    ) -> str:
        """
        Generate recommendation text based on achievements.

        Args:
            achievements: List of achievements
            recommender_context: Context about the recommender

        Returns:
            Recommendation text template
        """
        if not achievements:
            return ""

        # Calculate highlights
        total_impact = sum(a.impact_score or 0 for a in achievements)
        top_skills = self._get_top_skills(achievements, 5)
        categories = list(set(a.category for a in achievements))

        text = f"""
I highly recommend [Name] based on their exceptional track record of delivering impactful solutions.

Key Strengths:
• Demonstrated expertise in {", ".join(top_skills)}
• Proven ability to deliver high-impact projects (cumulative score: {total_impact})
• Versatile problem-solver across {len(categories)} technical domains

Notable Achievements:
{chr(10).join(f"• {a.title}" for a in sorted(achievements, key=lambda x: x.impact_score or 0, reverse=True)[:3])}

[Name] consistently delivers beyond expectations, combining technical excellence with business acumen. 
Their ability to tackle complex challenges and deliver measurable results makes them an invaluable asset to any team.

{recommender_context if recommender_context else ""}
"""

        return text.strip()

    def _get_top_skills(self, achievements: List, limit: int = 5) -> List[str]:
        """Get top skills from achievements."""
        skill_counts = {}
        for achievement in achievements:
            if achievement.skills_demonstrated:
                for skill in achievement.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return [skill[0] for skill in sorted_skills[:limit]]

    def format_for_profile_update(self, achievements: List) -> Dict[str, str]:
        """
        Format achievements for LinkedIn profile sections.

        Args:
            achievements: List of achievements

        Returns:
            Dictionary with formatted content for different profile sections
        """
        sections = {
            "headline": self._generate_headline(achievements),
            "about": self._generate_about_section(achievements),
            "featured": self._select_featured_achievements(achievements),
        }

        return sections

    def _generate_headline(self, achievements: List) -> str:
        """Generate professional headline."""
        if not achievements:
            return "Software Developer"

        top_skills = self._get_top_skills(achievements, 3)

        # Determine expertise level
        if len(achievements) >= 50:
            level = "Senior"
        elif len(achievements) >= 20:
            level = "Experienced"
        else:
            level = ""

        headline = f"{level} Software Engineer"
        if top_skills:
            headline += f" | {' • '.join(top_skills)}"

        return headline

    def _generate_about_section(self, achievements: List) -> str:
        """Generate About section content."""
        if not achievements:
            return ""

        total_impact = sum(a.impact_score or 0 for a in achievements)
        skill_count = len(
            set(
                skill
                for a in achievements
                if a.skills_demonstrated
                for skill in a.skills_demonstrated
            )
        )

        about = f"""
Passionate software engineer with a proven track record of delivering high-impact solutions.

🚀 Professional Highlights:
• {len(achievements)} documented achievements with cumulative impact score of {total_impact}
• Expertise across {skill_count} technologies and frameworks
• Consistent delivery of complex projects that drive business value

💡 Core Competencies:
{chr(10).join(f"• {skill}" for skill in self._get_top_skills(achievements, 8))}

🎯 Approach:
I believe in writing clean, maintainable code that solves real business problems. 
My experience spans {len(set(a.category for a in achievements))} technical domains, 
allowing me to bring a holistic perspective to every project.

Always eager to tackle new challenges and contribute to innovative solutions.
"""

        return about.strip()

    def _select_featured_achievements(self, achievements: List) -> List[Dict[str, str]]:
        """Select achievements for Featured section."""
        featured = []

        # Select top 3 achievements
        top_achievements = sorted(
            achievements, key=lambda a: a.impact_score or 0, reverse=True
        )[:3]

        for achievement in top_achievements:
            featured.append(
                {
                    "title": achievement.title,
                    "description": achievement.description or "",
                    "link": achievement.source_url,
                    "media": None,  # Could be screenshot/demo link
                }
            )

        return featured
