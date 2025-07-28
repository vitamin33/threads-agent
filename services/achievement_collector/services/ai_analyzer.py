"""Enhanced AI analysis for achievements using GPT-4."""

import os
from typing import Dict

import openai

from ..db.models import Achievement


class AIAnalyzer:
    """Enhanced AI analysis for achievements using GPT-4."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key and self.api_key != "test":
            openai.api_key = self.api_key
            self.client = openai.AsyncOpenAI()
        else:
            self.client = None

    async def analyze_achievement_impact(self, achievement: Achievement) -> Dict:
        """Perform deep analysis of achievement impact."""
        if not self.client:
            return self._mock_analysis(achievement)

        prompt = f"""
        Analyze this professional achievement and provide insights:
        
        Title: {achievement.title}
        Category: {achievement.category}
        Description: {achievement.description}
        Metrics: {achievement.metrics}
        Technologies: {", ".join(achievement.technologies or [])}
        Business Value: {achievement.business_value}
        
        Provide:
        1. Quantified impact score (0-100)
        2. Key strengths demonstrated
        3. Transferable skills highlighted
        4. Potential career advancement implications
        5. Suggested improvements or follow-up achievements
        6. Industry relevance and market value
        
        Format as JSON with these keys: impact_score, strengths, skills, career_implications, next_steps, market_value
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career coach and achievement analyst.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._mock_analysis(achievement)

    async def generate_professional_summary(self, achievements: list) -> str:
        """Generate a professional summary based on achievements."""
        if not self.api_key or self.api_key == "test":
            return self._mock_professional_summary(achievements)

        try:
            # Prepare achievement data
            achievement_data = []
            for a in achievements[:10]:  # Limit to top 10
                achievement_data.append(
                    {
                        "title": a.title,
                        "impact": a.impact_score,
                        "skills": a.skills_demonstrated,
                        "category": a.category,
                    }
                )

            prompt = f"""Based on these achievements, generate a professional summary (3-4 sentences):
            {achievement_data}
            
            Focus on key skills, impact, and professional strengths."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI summary generation failed: {e}")
            return self._mock_professional_summary(achievements)

    def _mock_professional_summary(self, achievements: list) -> str:
        """Mock professional summary for offline mode."""
        if not achievements:
            return "Experienced professional with a track record of delivering impactful results."

        # Extract top skills
        skill_counts = {}
        for a in achievements:
            if a.skills_demonstrated:
                for skill in a.skills_demonstrated:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        skills_text = ", ".join([skill[0] for skill in top_skills])

        return f"Results-driven professional with expertise in {skills_text}. Proven track record of delivering {len(achievements)} significant achievements with measurable business impact. Strong focus on innovation, optimization, and continuous improvement."

    async def generate_linkedin_content(self, achievement) -> str:
        """Generate LinkedIn post content for an achievement."""
        if not self.api_key or self.api_key == "test":
            return self._mock_linkedin_content(achievement)

        try:
            prompt = f"""Create an engaging LinkedIn post about this achievement:
            Title: {achievement.title}
            Description: {achievement.description}
            Impact: {achievement.impact_score}
            Skills: {achievement.skills_demonstrated}
            
            Make it professional, engaging, and authentic. Include a call to action."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI LinkedIn content generation failed: {e}")
            return self._mock_linkedin_content(achievement)

    def _mock_linkedin_content(self, achievement) -> str:
        """Mock LinkedIn content for offline mode."""
        return f"🚀 Excited to share a recent achievement: {achievement.title}\n\n{achievement.description}\n\n💡 Key takeaway: Continuous improvement and innovation drive real business impact.\n\n#TechInnovation #ContinuousImprovement #ProfessionalGrowth"

    def _mock_analysis(self, achievement: Achievement) -> Dict:
        """Mock analysis for offline mode."""
        return {
            "impact_score": 85,
            "strengths": ["Technical excellence", "Business impact", "Innovation"],
            "skills": ["Python", "AI/ML", "System optimization", "Leadership"],
            "career_implications": "Strong candidate for senior engineering roles",
            "next_steps": [
                "Scale solution to larger datasets",
                "Present at conferences",
            ],
            "market_value": "High demand - $150k-$200k range",
        }
