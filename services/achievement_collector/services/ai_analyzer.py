# AI-Powered Achievement Analyzer

import json
from decimal import Decimal
from typing import List

import httpx
from api.schemas import AnalysisResponse
from core.logging import setup_logging
from db.models import Achievement

logger = setup_logging(__name__)


class AchievementAnalyzer:
    """AI-powered achievement analysis service"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def analyze(
        self,
        achievement: Achievement,
        analyze_impact: bool = True,
        analyze_technical: bool = True,
        generate_summary: bool = True,
    ) -> AnalysisResponse:
        """Analyze achievement using AI"""

        # Build context
        context = self._build_context(achievement)

        # Generate analyses
        results = {}

        if generate_summary:
            results["summary"] = await self._generate_summary(context)

        if analyze_impact:
            impact_data = await self._analyze_impact(context)
            results.update(impact_data)

        if analyze_technical:
            results["technical_analysis"] = await self._analyze_technical(context)

        # Calculate scores
        impact_score = self._calculate_impact_score(results, achievement)
        complexity_score = self._calculate_complexity_score(results, achievement)

        # Extract metrics
        business_value = results.get("business_value", 0)
        time_saved_hours = results.get("time_saved_hours", 0)

        return AnalysisResponse(
            achievement_id=achievement.id,
            impact_score=impact_score,
            complexity_score=complexity_score,
            business_value=Decimal(str(business_value)),
            time_saved_hours=time_saved_hours,
            summary=results.get("summary", ""),
            impact_analysis=results.get("impact_analysis", ""),
            technical_analysis=results.get("technical_analysis", ""),
            recommendations=results.get("recommendations", []),
        )

    def _build_context(self, achievement: Achievement) -> str:
        """Build context for AI analysis"""

        return f"""
        Achievement: {achievement.title}
        Description: {achievement.description}
        Category: {achievement.category}
        Duration: {achievement.duration_hours} hours
        
        Tags: {", ".join(achievement.tags)}
        Skills: {", ".join(achievement.skills_demonstrated)}
        
        Evidence: {json.dumps(achievement.evidence, indent=2)}
        Metrics Before: {json.dumps(achievement.metrics_before, indent=2)}
        Metrics After: {json.dumps(achievement.metrics_after, indent=2)}
        """

    async def _generate_summary(self, context: str) -> str:
        """Generate professional summary"""

        prompt = f"""
        Based on this achievement, write a professional summary suitable for a portfolio.
        Focus on impact, technical skills, and business value.
        Keep it concise (2-3 sentences).
        
        {context}
        """

        response = await self._call_openai(prompt)
        return response.strip()

    async def _analyze_impact(self, context: str) -> dict:
        """Analyze business impact"""

        prompt = f"""
        Analyze the business impact of this achievement.
        
        Provide:
        1. Impact analysis (2-3 paragraphs)
        2. Estimated business value in dollars
        3. Estimated time saved per month in hours
        4. 3-5 specific recommendations
        
        Return as JSON with keys: impact_analysis, business_value, time_saved_hours, recommendations
        
        {context}
        """

        response = await self._call_openai(prompt, json_mode=True)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse impact analysis JSON: {response}")
            return {
                "impact_analysis": response,
                "business_value": 0,
                "time_saved_hours": 0,
                "recommendations": [],
            }

    async def _analyze_technical(self, context: str) -> str:
        """Analyze technical approach"""

        prompt = f"""
        Analyze the technical approach and implementation of this achievement.
        Focus on:
        - Technical complexity and challenges
        - Architectural decisions
        - Best practices demonstrated
        - Innovation and creativity
        
        Write 2-3 paragraphs.
        
        {context}
        """

        response = await self._call_openai(prompt)
        return response.strip()

    async def _call_openai(self, prompt: str, json_mode: bool = False) -> str:
        """Call OpenAI API"""

        if not self.api_key or self.api_key == "test":
            # Return mock response for testing
            if json_mode:
                return json.dumps(
                    {
                        "impact_analysis": "Significant impact on system performance",
                        "business_value": 50000,
                        "time_saved_hours": 20,
                        "recommendations": [
                            "Continue optimization",
                            "Document process",
                        ],
                    }
                )
            return "This achievement demonstrates strong technical skills and business impact."

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional achievement analyst.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def _calculate_impact_score(self, results: dict, achievement: Achievement) -> float:
        """Calculate impact score (0-100)"""

        score = 0.0

        # Business value component (0-40 points)
        business_value = float(results.get("business_value", 0))
        if business_value >= 100000:
            score += 40
        elif business_value >= 50000:
            score += 30
        elif business_value >= 10000:
            score += 20
        elif business_value >= 1000:
            score += 10

        # Time saved component (0-30 points)
        time_saved = results.get("time_saved_hours", 0)
        if time_saved >= 100:
            score += 30
        elif time_saved >= 50:
            score += 20
        elif time_saved >= 10:
            score += 10

        # Category bonus (0-20 points)
        category_scores = {
            "architecture": 20,
            "optimization": 18,
            "feature": 15,
            "security": 15,
            "infrastructure": 12,
            "performance": 12,
            "bugfix": 10,
            "testing": 8,
            "documentation": 5,
        }
        score += category_scores.get(achievement.category, 10)

        # Evidence bonus (0-10 points)
        if achievement.metrics_after:
            score += 5
        if achievement.evidence:
            score += 5

        return min(score, 100.0)

    def _calculate_complexity_score(
        self, results: dict, achievement: Achievement
    ) -> float:
        """Calculate technical complexity score (0-100)"""

        score = 0.0

        # Duration component (0-30 points)
        if achievement.duration_hours >= 40:
            score += 30
        elif achievement.duration_hours >= 20:
            score += 20
        elif achievement.duration_hours >= 10:
            score += 10

        # Skills component (0-30 points)
        skill_count = len(achievement.skills_demonstrated)
        score += min(skill_count * 5, 30)

        # Category complexity (0-20 points)
        category_scores = {
            "architecture": 20,
            "security": 18,
            "performance": 15,
            "infrastructure": 15,
            "optimization": 12,
            "feature": 10,
            "bugfix": 8,
            "testing": 5,
            "documentation": 3,
        }
        score += category_scores.get(achievement.category, 10)

        # Technical analysis length (0-20 points)
        tech_analysis = results.get("technical_analysis", "")
        if len(tech_analysis) > 500:
            score += 20
        elif len(tech_analysis) > 300:
            score += 10

        return min(score, 100.0)

    async def generate_portfolio_insights(
        self, achievements: List[Achievement]
    ) -> List[str]:
        """Generate insights across multiple achievements"""

        context = "\n\n".join(
            [
                f"- {a.title}: {a.ai_summary or a.description[:100]}..."
                for a in achievements
            ]
        )

        prompt = f"""
        Based on these achievements, provide 5-7 key insights that demonstrate:
        - Technical expertise and growth
        - Business impact and value creation
        - Problem-solving abilities
        - Leadership and collaboration
        
        Achievements:
        {context}
        
        Return as a JSON array of insight strings.
        """

        response = await self._call_openai(prompt, json_mode=True)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return [
                "Strong technical skills demonstrated",
                "Significant business impact achieved",
            ]
