"""
Industry Benchmarking - Compare achievements against industry standards.

This module provides benchmarking capabilities to compare individual achievements
and career progression against industry averages and top performers.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.models import Achievement


class IndustryBenchmark(BaseModel):
    """Industry benchmark data for a specific metric."""

    metric_name: str
    your_value: float
    industry_average: float
    industry_median: float
    top_10_percent: float
    top_25_percent: float
    percentile: int  # Your percentile rank (0-100)
    trend: str  # "improving", "stable", "declining"
    recommendation: str


class CompensationBenchmark(BaseModel):
    """Salary and compensation benchmarking data."""

    role: str
    years_experience: float
    location: str
    your_estimated_value: int
    market_low: int
    market_median: int
    market_high: int
    percentile: int
    factors: Dict[str, float]  # Factors affecting compensation


class SkillMarketData(BaseModel):
    """Market data for specific skills."""

    skill_name: str
    demand_level: float  # 0-10
    supply_level: float  # 0-10
    market_ratio: float  # demand/supply
    average_premium: float  # Salary premium percentage
    job_postings: int
    growth_rate: float  # YoY growth
    future_outlook: str  # "declining", "stable", "growing", "explosive"


class IndustryBenchmarker:
    """Benchmark achievements and career metrics against industry standards."""

    def __init__(self):
        # In production, these would come from real market data APIs
        self.industry_data = self._load_industry_data()

    def benchmark_achievements(
        self, db: Session, user_id: Optional[str] = None, time_period_days: int = 365
    ) -> List[IndustryBenchmark]:
        """
        Benchmark user achievements against industry standards.

        Args:
            db: Database session
            user_id: Optional user filter
            time_period_days: Period to analyze (default 1 year)

        Returns:
            List of benchmark comparisons
        """
        # Get user achievements
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        query = db.query(Achievement).filter(Achievement.completed_at >= cutoff_date)
        if user_id:
            query = query.filter(Achievement.user_id == user_id)

        achievements = query.all()

        # Calculate user metrics
        metrics = self._calculate_user_metrics(achievements, time_period_days)

        # Benchmark each metric
        benchmarks = []
        for metric_name, user_value in metrics.items():
            benchmark = self._benchmark_metric(metric_name, user_value)
            benchmarks.append(benchmark)

        return benchmarks

    def _calculate_user_metrics(
        self, achievements: List[Achievement], time_period_days: int
    ) -> Dict[str, float]:
        """Calculate various metrics from achievements."""
        if not achievements:
            return {}

        months = time_period_days / 30

        metrics = {
            "achievements_per_month": len(achievements) / months,
            "average_impact_score": np.mean(
                [a.impact_score for a in achievements if a.impact_score is not None]
            )
            if achievements
            else 0,
            "high_impact_achievements": len(
                [a for a in achievements if (a.impact_score or 0) >= 80]
            )
            / months,
            "skill_diversity": len(
                set(
                    skill
                    for a in achievements
                    if a.skills_demonstrated
                    for skill in a.skills_demonstrated
                )
            ),
            "technical_depth": np.mean(
                [
                    a.complexity_score
                    for a in achievements
                    if a.complexity_score is not None
                ]
            )
            if achievements
            else 0,
        }

        # Calculate category distribution
        category_counts = {}
        for a in achievements:
            category_counts[a.category] = category_counts.get(a.category, 0) + 1

        # Add category-specific metrics
        for category, count in category_counts.items():
            metrics[f"{category}_achievements"] = count / months

        return metrics

    def _benchmark_metric(
        self, metric_name: str, user_value: float
    ) -> IndustryBenchmark:
        """Benchmark a single metric against industry data."""
        # Get industry data for this metric
        industry_stats = self.industry_data.get(
            metric_name,
            {
                "average": 3.0,
                "median": 2.5,
                "percentiles": {10: 1.0, 25: 2.0, 50: 2.5, 75: 4.0, 90: 6.0},
            },
        )

        # Calculate percentile
        percentile = self._calculate_percentile(
            user_value, industry_stats["percentiles"]
        )

        # Determine trend
        trend = self._determine_trend(metric_name, user_value, percentile)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            metric_name, user_value, percentile
        )

        return IndustryBenchmark(
            metric_name=metric_name,
            your_value=round(user_value, 2),
            industry_average=industry_stats["average"],
            industry_median=industry_stats["median"],
            top_10_percent=industry_stats["percentiles"][90],
            top_25_percent=industry_stats["percentiles"][75],
            percentile=percentile,
            trend=trend,
            recommendation=recommendation,
        )

    def _calculate_percentile(self, value: float, percentiles: Dict[int, float]) -> int:
        """Calculate percentile rank based on value."""
        if value <= percentiles[10]:
            return int(value / percentiles[10] * 10)
        elif value <= percentiles[25]:
            return 10 + int(
                (value - percentiles[10]) / (percentiles[25] - percentiles[10]) * 15
            )
        elif value <= percentiles[50]:
            return 25 + int(
                (value - percentiles[25]) / (percentiles[50] - percentiles[25]) * 25
            )
        elif value <= percentiles[75]:
            return 50 + int(
                (value - percentiles[50]) / (percentiles[75] - percentiles[50]) * 25
            )
        elif value <= percentiles[90]:
            return 75 + int(
                (value - percentiles[75]) / (percentiles[90] - percentiles[75]) * 15
            )
        else:
            return min(90 + int((value - percentiles[90]) / percentiles[90] * 10), 99)

    def _determine_trend(
        self, metric_name: str, current_value: float, percentile: int
    ) -> str:
        """Determine if metric is trending up, down, or stable."""
        # In production, this would analyze historical data
        if percentile >= 75:
            return "improving"
        elif percentile <= 25:
            return "declining"
        else:
            return "stable"

    def _generate_recommendation(
        self, metric_name: str, user_value: float, percentile: int
    ) -> str:
        """Generate actionable recommendation based on benchmark."""
        if percentile >= 90:
            return f"Excellent! You're in the top 10% for {metric_name}. Consider mentoring others."
        elif percentile >= 75:
            return "Great performance! Focus on consistency to reach the top 10%."
        elif percentile >= 50:
            return "Above average. Increase frequency or impact to improve further."
        elif percentile >= 25:
            return f"Room for improvement. Set weekly goals for {metric_name}."
        else:
            return f"Significant opportunity. Consider focusing on {metric_name} as a priority."

    async def benchmark_compensation(
        self,
        role: str,
        years_experience: float,
        skills: List[str],
        location: str = "Remote",
        achievements_count: int = 0,
    ) -> CompensationBenchmark:
        """
        Benchmark compensation based on role, experience, and achievements.

        Args:
            role: Job title/role
            years_experience: Years of experience
            skills: List of skills
            location: Geographic location
            achievements_count: Number of significant achievements

        Returns:
            Compensation benchmark data
        """
        # Base salary by role and experience
        base_salary = self._get_base_salary(role, years_experience)

        # Calculate skill premiums
        skill_premium = (
            sum(self._get_skill_premium(skill) for skill in skills) / 100
        )  # Convert to multiplier

        # Location adjustment
        location_multiplier = self._get_location_multiplier(location)

        # Achievement bonus
        achievement_multiplier = 1 + (achievements_count * 0.02)  # 2% per achievement

        # Calculate final estimate
        estimated_value = int(
            base_salary
            * (1 + skill_premium)
            * location_multiplier
            * achievement_multiplier
        )

        # Get market ranges
        market_data = self._get_market_data(role, years_experience)

        # Calculate percentile
        percentile = self._calculate_salary_percentile(estimated_value, market_data)

        return CompensationBenchmark(
            role=role,
            years_experience=years_experience,
            location=location,
            your_estimated_value=estimated_value,
            market_low=market_data["low"],
            market_median=market_data["median"],
            market_high=market_data["high"],
            percentile=percentile,
            factors={
                "base_salary": base_salary,
                "skill_premium": skill_premium,
                "location_multiplier": location_multiplier,
                "achievement_multiplier": achievement_multiplier,
            },
        )

    def analyze_skill_market(self, skills: List[str]) -> List[SkillMarketData]:
        """
        Analyze market conditions for specific skills.

        Args:
            skills: List of skill names

        Returns:
            Market data for each skill
        """
        market_data = []

        for skill in skills:
            # In production, this would query real job market APIs
            data = self._get_skill_market_data(skill)

            market_data.append(
                SkillMarketData(
                    skill_name=skill,
                    demand_level=data["demand"],
                    supply_level=data["supply"],
                    market_ratio=data["demand"] / max(data["supply"], 0.1),
                    average_premium=data["premium"],
                    job_postings=data["postings"],
                    growth_rate=data["growth"],
                    future_outlook=self._determine_outlook(data),
                )
            )

        return market_data

    def _load_industry_data(self) -> Dict:
        """Load industry benchmark data."""
        # In production, this would load from a database or API
        return {
            "achievements_per_month": {
                "average": 3.0,
                "median": 2.5,
                "percentiles": {10: 0.5, 25: 1.5, 50: 2.5, 75: 4.0, 90: 6.0},
            },
            "average_impact_score": {
                "average": 65,
                "median": 60,
                "percentiles": {10: 40, 25: 50, 50: 60, 75: 75, 90: 85},
            },
            "skill_diversity": {
                "average": 15,
                "median": 12,
                "percentiles": {10: 5, 25: 8, 50: 12, 75: 20, 90: 30},
            },
        }

    def _get_base_salary(self, role: str, years_exp: float) -> int:
        """Get base salary for role and experience."""
        # Simplified salary calculation
        role_bases = {
            "Software Engineer": 100000,
            "Senior Software Engineer": 130000,
            "Staff Engineer": 160000,
            "Principal Engineer": 200000,
            "Engineering Manager": 150000,
            "Director of Engineering": 200000,
            "VP of Engineering": 250000,
        }

        base = role_bases.get(role, 100000)
        experience_multiplier = 1 + (years_exp * 0.05)  # 5% per year

        return int(base * experience_multiplier)

    def _get_skill_premium(self, skill: str) -> float:
        """Get salary premium percentage for a skill."""
        premium_skills = {
            "AI/ML": 20,
            "Kubernetes": 15,
            "AWS": 10,
            "React": 8,
            "Python": 5,
            "Leadership": 15,
            "Architecture": 12,
        }

        return premium_skills.get(skill, 3)  # Default 3% premium

    def _get_location_multiplier(self, location: str) -> float:
        """Get location-based salary multiplier."""
        location_multipliers = {
            "San Francisco": 1.4,
            "New York": 1.3,
            "Seattle": 1.2,
            "Austin": 1.1,
            "Remote": 1.0,
            "Denver": 0.95,
            "Atlanta": 0.9,
        }

        return location_multipliers.get(location, 1.0)

    def _get_market_data(self, role: str, years_exp: float) -> Dict:
        """Get market salary ranges."""
        base = self._get_base_salary(role, years_exp)

        return {"low": int(base * 0.8), "median": base, "high": int(base * 1.3)}

    def _calculate_salary_percentile(self, salary: int, market_data: Dict) -> int:
        """Calculate salary percentile within market range."""
        if salary <= market_data["low"]:
            return int(salary / market_data["low"] * 25)
        elif salary <= market_data["median"]:
            return 25 + int(
                (salary - market_data["low"])
                / (market_data["median"] - market_data["low"])
                * 25
            )
        elif salary <= market_data["high"]:
            return 50 + int(
                (salary - market_data["median"])
                / (market_data["high"] - market_data["median"])
                * 40
            )
        else:
            return min(
                90 + int((salary - market_data["high"]) / market_data["high"] * 10), 99
            )

    def _get_skill_market_data(self, skill: str) -> Dict:
        """Get market data for a specific skill."""
        # Simulated market data
        market_data = {
            "AI/ML": {
                "demand": 9.5,
                "supply": 3.0,
                "premium": 25,
                "postings": 15000,
                "growth": 45,
            },
            "Kubernetes": {
                "demand": 8.0,
                "supply": 4.0,
                "premium": 15,
                "postings": 12000,
                "growth": 30,
            },
            "Python": {
                "demand": 7.5,
                "supply": 7.0,
                "premium": 5,
                "postings": 25000,
                "growth": 10,
            },
        }

        return market_data.get(
            skill,
            {"demand": 5.0, "supply": 5.0, "premium": 3, "postings": 5000, "growth": 5},
        )

    def _determine_outlook(self, data: Dict) -> str:
        """Determine future outlook for a skill."""
        if data["growth"] > 30 and data["demand"] / data["supply"] > 2:
            return "explosive"
        elif data["growth"] > 15:
            return "growing"
        elif data["growth"] < -10:
            return "declining"
        else:
            return "stable"
