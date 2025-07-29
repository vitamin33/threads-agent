"""
Career Predictor - AI-powered career trajectory analysis.

This module provides predictive analytics for career development based on
achievement history, skill progression, and industry trends.
"""

from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.models import Achievement
from ..services.ai_analyzer import AIAnalyzer


class CareerPrediction(BaseModel):
    """Career prediction model with confidence scores."""

    next_role: str
    confidence: float  # 0.0 to 1.0
    timeline_months: int
    required_skills: List[str]
    recommended_achievements: List[str]
    salary_range: Tuple[int, int]
    market_demand: str  # "low", "medium", "high", "very_high"


class SkillProgression(BaseModel):
    """Model for tracking skill development over time."""

    skill_name: str
    current_level: int  # 1-10
    growth_rate: float  # skill points per month
    market_value: float  # relative market value 0-1
    trending: bool
    next_milestone: str


class CareerInsights(BaseModel):
    """Comprehensive career insights based on achievements."""

    current_level: str  # "junior", "mid", "senior", "lead", "principal"
    years_experience: float
    top_skills: List[SkillProgression]
    career_velocity: float  # career progression speed vs industry average
    market_position: float  # percentile in market (0-100)
    strengths: List[str]
    improvement_areas: List[str]


class CareerPredictor:
    """Advanced career prediction and trajectory analysis."""

    def __init__(self, ai_analyzer: Optional[AIAnalyzer] = None):
        self.ai_analyzer = ai_analyzer or AIAnalyzer()

    async def predict_career_trajectory(
        self, db: Session, user_id: Optional[str] = None, time_horizon_months: int = 24
    ) -> List[CareerPrediction]:
        """
        Predict career trajectory for the next N months.

        Args:
            db: Database session
            user_id: Optional user filter
            time_horizon_months: How far to predict (default 24 months)

        Returns:
            List of career predictions with timelines
        """
        # Get achievement history
        query = db.query(Achievement)
        if user_id:
            query = query.filter(Achievement.user_id == user_id)
        achievements = query.order_by(Achievement.completed_at.desc()).all()

        if not achievements:
            return []

        # Analyze skill progression
        skills = self._analyze_skill_progression(achievements)

        # Calculate career velocity
        velocity = self._calculate_career_velocity(achievements)

        # Generate predictions using AI
        predictions = await self._generate_ai_predictions(
            achievements, skills, velocity, time_horizon_months
        )

        return predictions

    def _analyze_skill_progression(
        self, achievements: List[Achievement]
    ) -> Dict[str, SkillProgression]:
        """Analyze how skills have progressed over time."""
        skill_timeline = {}

        for achievement in achievements:
            if not achievement.skills_demonstrated:
                continue

            for skill in achievement.skills_demonstrated:
                if skill not in skill_timeline:
                    skill_timeline[skill] = []

                skill_timeline[skill].append(
                    {
                        "date": achievement.completed_at,
                        "complexity": achievement.complexity_score or 50,
                        "impact": achievement.impact_score or 50,
                    }
                )

        # Calculate progression for each skill
        progressions = {}
        for skill, timeline in skill_timeline.items():
            if len(timeline) < 2:
                continue

            # Sort by date
            timeline.sort(key=lambda x: x["date"])

            # Calculate growth rate
            time_span = (timeline[-1]["date"] - timeline[0]["date"]).days / 30  # months
            skill_growth = (
                timeline[-1]["complexity"] - timeline[0]["complexity"]
            ) / 100

            growth_rate = skill_growth / max(time_span, 1)

            progressions[skill] = SkillProgression(
                skill_name=skill,
                current_level=min(int(timeline[-1]["complexity"] / 10), 10),
                growth_rate=growth_rate,
                market_value=self._get_skill_market_value(skill),
                trending=self._is_skill_trending(skill),
                next_milestone=self._get_next_milestone(
                    skill, timeline[-1]["complexity"]
                ),
            )

        return progressions

    def _calculate_career_velocity(self, achievements: List[Achievement]) -> float:
        """
        Calculate career progression velocity compared to industry average.

        Returns:
            Velocity multiplier (1.0 = average, >1.0 = faster than average)
        """
        if len(achievements) < 2:
            return 1.0

        # Calculate average time between significant achievements
        significant_achievements = [
            a for a in achievements if (a.impact_score or 0) >= 70
        ]

        if len(significant_achievements) < 2:
            return 1.0

        time_gaps = []
        for i in range(1, len(significant_achievements)):
            gap = (
                significant_achievements[i - 1].completed_at
                - significant_achievements[i].completed_at
            ).days
            time_gaps.append(gap)

        avg_gap = sum(time_gaps) / len(time_gaps)

        # Industry average is ~90 days between significant achievements
        industry_avg = 90
        velocity = industry_avg / max(avg_gap, 1)

        return min(max(velocity, 0.5), 3.0)  # Cap between 0.5x and 3x

    async def _generate_ai_predictions(
        self,
        achievements: List[Achievement],
        skills: Dict[str, SkillProgression],
        velocity: float,
        time_horizon_months: int,
    ) -> List[CareerPrediction]:
        """Use AI to generate career predictions."""
        # Prepare context for AI
        achievement_summary = self._summarize_achievements(achievements)
        skill_summary = self._summarize_skills(skills)

        prompt = f"""
        Based on the following career data, predict the next career moves:
        
        Achievement Summary:
        {achievement_summary}
        
        Skills and Growth:
        {skill_summary}
        
        Career Velocity: {velocity}x industry average
        Time Horizon: {time_horizon_months} months
        
        Provide 3 career predictions in JSON format with these fields:
        - next_role: Specific job title
        - confidence: 0.0 to 1.0
        - timeline_months: When this could happen
        - required_skills: List of skills needed
        - recommended_achievements: Specific achievements to pursue
        - salary_range: [min, max] in USD
        - market_demand: "low", "medium", "high", or "very_high"
        """

        # Call OpenAI directly if available
        if self.ai_analyzer.client:
            response = await self.ai_analyzer.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            predictions_data = eval(response.choices[0].message.content)
        else:
            # Mock response for testing
            predictions_data = {
                "predictions": [
                    {
                        "next_role": "Senior Software Engineer",
                        "confidence": 0.75,
                        "timeline_months": 18,
                        "required_skills": ["System Design", "Leadership"],
                        "recommended_achievements": ["Lead a team project"],
                        "salary_range": [120000, 150000],
                        "market_demand": "high",
                    }
                ]
            }

        # Parse AI response and create predictions
        predictions = []
        for pred_data in predictions_data.get("predictions", []):
            predictions.append(
                CareerPrediction(
                    next_role=pred_data["next_role"],
                    confidence=pred_data["confidence"],
                    timeline_months=pred_data["timeline_months"],
                    required_skills=pred_data["required_skills"],
                    recommended_achievements=pred_data["recommended_achievements"],
                    salary_range=tuple(pred_data["salary_range"]),
                    market_demand=pred_data["market_demand"],
                )
            )

        return predictions

    def _summarize_achievements(self, achievements: List[Achievement]) -> str:
        """Create a summary of achievements for AI context."""
        categories = {}
        for a in achievements:
            if a.category not in categories:
                categories[a.category] = 0
            categories[a.category] += 1

        summary = f"Total: {len(achievements)} achievements\n"
        summary += "Categories: " + ", ".join(
            f"{cat}: {count}" for cat, count in categories.items()
        )

        # Add recent highlights
        recent = achievements[:5]
        if recent:
            summary += "\n\nRecent highlights:\n"
            for a in recent:
                summary += f"- {a.title} (Impact: {a.impact_score})\n"

        return summary

    def _summarize_skills(self, skills: Dict[str, SkillProgression]) -> str:
        """Create a summary of skills for AI context."""
        if not skills:
            return "No skill progression data available"

        top_skills = sorted(
            skills.values(),
            key=lambda s: s.current_level * s.market_value,
            reverse=True,
        )[:10]

        summary = "Top Skills:\n"
        for skill in top_skills:
            trend = "📈" if skill.trending else "→"
            summary += (
                f"- {skill.skill_name}: Level {skill.current_level}/10 "
                f"{trend} (Growth: {skill.growth_rate:.2f}/month)\n"
            )

        return summary

    def _get_skill_market_value(self, skill: str) -> float:
        """Get relative market value for a skill (0-1)."""
        # In production, this would query real market data
        high_value_skills = {
            "AI/ML",
            "Kubernetes",
            "Cloud Architecture",
            "DevOps",
            "Data Engineering",
            "Security",
            "Blockchain",
            "React",
        }

        if skill in high_value_skills:
            return 0.9
        elif any(term in skill.lower() for term in ["python", "java", "aws"]):
            return 0.7
        else:
            return 0.5

    def _is_skill_trending(self, skill: str) -> bool:
        """Check if a skill is trending in the market."""
        # In production, this would check real trend data
        trending_skills = {
            "AI/ML",
            "GenAI",
            "LLM",
            "Kubernetes",
            "Rust",
            "WebAssembly",
            "Edge Computing",
            "Quantum Computing",
        }
        return skill in trending_skills

    def _get_next_milestone(self, skill: str, current_level: float) -> str:
        """Get the next milestone for a skill."""
        level = int(current_level / 10)

        milestones = {
            1: "Complete first production project",
            2: "Build intermediate-level application",
            3: "Lead a team project",
            4: "Architect a system",
            5: "Mentor others",
            6: "Speak at conferences",
            7: "Publish technical articles",
            8: "Contribute to major open source",
            9: "Industry recognition",
            10: "Thought leadership",
        }

        return milestones.get(min(level + 1, 10), "Master level achieved")

    async def analyze_skill_gaps(
        self, db: Session, target_role: str, user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Analyze skill gaps for a target role.

        Args:
            db: Database session
            target_role: Target job role
            user_id: Optional user filter

        Returns:
            Dictionary with skill gap analysis
        """
        # Get current skills from achievements
        query = db.query(Achievement)
        if user_id:
            query = query.filter(Achievement.user_id == user_id)
        achievements = query.all()

        current_skills = set()
        for a in achievements:
            if a.skills_demonstrated:
                current_skills.update(a.skills_demonstrated)

        # Get required skills for target role using AI
        prompt = f"""
        List the top 10 required skills for a {target_role} position.
        Include both technical and soft skills.
        Format as JSON array of strings.
        """

        # Call OpenAI directly if available
        if self.ai_analyzer.client:
            response = await self.ai_analyzer.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            response_data = eval(response.choices[0].message.content)
        else:
            # Mock response for testing
            response_data = {
                "skills": [
                    "Python",
                    "AWS",
                    "Kubernetes",
                    "System Design",
                    "Leadership",
                    "Communication",
                    "Project Management",
                    "Data Analysis",
                    "CI/CD",
                    "Monitoring",
                ]
            }

        response = response_data

        required_skills = set(response.get("skills", []))

        # Calculate gaps
        missing_skills = required_skills - current_skills
        existing_skills = required_skills & current_skills

        return {
            "target_role": target_role,
            "required_skills": list(required_skills),
            "current_skills": list(current_skills),
            "missing_skills": list(missing_skills),
            "skill_coverage": len(existing_skills) / len(required_skills)
            if required_skills
            else 0,
            "recommendations": self._generate_skill_recommendations(missing_skills),
        }

    def _generate_skill_recommendations(self, missing_skills: set) -> List[str]:
        """Generate recommendations for acquiring missing skills."""
        recommendations = []

        for skill in list(missing_skills)[:5]:  # Top 5 missing skills
            recommendations.append(
                {
                    "skill": skill,
                    "learning_path": f"Complete online course on {skill}",
                    "practice_project": f"Build a project demonstrating {skill}",
                    "timeline_weeks": 4 if "advanced" in skill.lower() else 2,
                }
            )

        return recommendations
