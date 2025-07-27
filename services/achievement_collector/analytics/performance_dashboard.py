"""
Performance Dashboard - Advanced analytics and visualization data.

This module provides comprehensive performance metrics and dashboard data
for career progression tracking and visualization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import Achievement


class TimeSeriesMetric(BaseModel):
    """Time series data point for metrics."""
    
    timestamp: datetime
    value: float
    label: Optional[str] = None


class SkillRadarData(BaseModel):
    """Data for skill radar/spider chart."""
    
    skill: str
    current_level: float  # 0-10
    industry_average: float  # 0-10
    growth_trend: float  # -1 to +1
    

class ImpactHeatmap(BaseModel):
    """Heatmap data for achievement impact over time."""
    
    week: str  # ISO week format
    category: str
    impact_score: float
    count: int


class CareerMilestone(BaseModel):
    """Significant career milestone."""
    
    date: datetime
    title: str
    description: str
    impact: str  # "low", "medium", "high", "critical"
    category: str
    

class DashboardMetrics(BaseModel):
    """Complete dashboard metrics package."""
    
    # Summary statistics
    total_achievements: int
    average_impact: float
    career_velocity: float
    skill_count: int
    
    # Time series data
    achievement_timeline: List[TimeSeriesMetric]
    impact_progression: List[TimeSeriesMetric]
    skill_growth: List[TimeSeriesMetric]
    
    # Categorical data
    category_distribution: Dict[str, int]
    skill_radar: List[SkillRadarData]
    impact_heatmap: List[ImpactHeatmap]
    
    # Milestones
    career_milestones: List[CareerMilestone]
    
    # Comparative metrics
    percentile_rank: int
    improvement_rate: float
    momentum_score: float


class PerformanceDashboard:
    """Generate comprehensive performance analytics and dashboard data."""
    
    def generate_dashboard_metrics(
        self,
        db: Session,
        user_id: Optional[str] = None,
        time_period_days: int = 365
    ) -> DashboardMetrics:
        """
        Generate complete dashboard metrics for visualization.
        
        Args:
            db: Database session
            user_id: Optional user filter
            time_period_days: Period to analyze
            
        Returns:
            Complete dashboard metrics
        """
        # Get achievements
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        query = db.query(Achievement).filter(
            Achievement.completed_at >= cutoff_date
        )
        if user_id:
            query = query.filter(Achievement.user_id == user_id)
            
        achievements = query.order_by(Achievement.completed_at).all()
        
        # Generate all metrics
        return DashboardMetrics(
            total_achievements=len(achievements),
            average_impact=self._calculate_average_impact(achievements),
            career_velocity=self._calculate_career_velocity(achievements),
            skill_count=self._count_unique_skills(achievements),
            achievement_timeline=self._generate_achievement_timeline(achievements),
            impact_progression=self._generate_impact_progression(achievements),
            skill_growth=self._generate_skill_growth(achievements),
            category_distribution=self._calculate_category_distribution(achievements),
            skill_radar=self._generate_skill_radar(achievements),
            impact_heatmap=self._generate_impact_heatmap(achievements),
            career_milestones=self._identify_career_milestones(achievements),
            percentile_rank=self._calculate_percentile_rank(achievements),
            improvement_rate=self._calculate_improvement_rate(achievements),
            momentum_score=self._calculate_momentum_score(achievements)
        )
    
    def _calculate_average_impact(self, achievements: List[Achievement]) -> float:
        """Calculate average impact score."""
        if not achievements:
            return 0.0
            
        impact_scores = [a.impact_score for a in achievements if a.impact_score]
        return np.mean(impact_scores) if impact_scores else 0.0
    
    def _calculate_career_velocity(self, achievements: List[Achievement]) -> float:
        """Calculate career progression velocity."""
        if len(achievements) < 2:
            return 1.0
            
        # Compare achievement rate over time
        first_half = achievements[:len(achievements)//2]
        second_half = achievements[len(achievements)//2:]
        
        first_rate = len(first_half) / max((first_half[-1].completed_at - 
                                           first_half[0].completed_at).days, 1)
        second_rate = len(second_half) / max((second_half[-1].completed_at - 
                                             second_half[0].completed_at).days, 1)
        
        velocity = second_rate / max(first_rate, 0.001)
        return round(min(max(velocity, 0.5), 3.0), 2)
    
    def _count_unique_skills(self, achievements: List[Achievement]) -> int:
        """Count unique skills demonstrated."""
        skills = set()
        for a in achievements:
            if a.skills_demonstrated:
                skills.update(a.skills_demonstrated)
        return len(skills)
    
    def _generate_achievement_timeline(
        self, 
        achievements: List[Achievement]
    ) -> List[TimeSeriesMetric]:
        """Generate achievement count timeline."""
        if not achievements:
            return []
            
        # Group by month
        timeline = {}
        for a in achievements:
            month_key = a.completed_at.strftime('%Y-%m')
            timeline[month_key] = timeline.get(month_key, 0) + 1
            
        # Convert to time series
        result = []
        for month, count in sorted(timeline.items()):
            result.append(TimeSeriesMetric(
                timestamp=datetime.strptime(month + '-01', '%Y-%m-%d'),
                value=count,
                label=f"{count} achievements"
            ))
            
        return result
    
    def _generate_impact_progression(
        self, 
        achievements: List[Achievement]
    ) -> List[TimeSeriesMetric]:
        """Generate impact score progression over time."""
        if not achievements:
            return []
            
        result = []
        cumulative_impact = 0
        
        for a in achievements:
            if a.impact_score:
                cumulative_impact += a.impact_score
                result.append(TimeSeriesMetric(
                    timestamp=a.completed_at,
                    value=cumulative_impact,
                    label=a.title
                ))
                
        return result
    
    def _generate_skill_growth(
        self, 
        achievements: List[Achievement]
    ) -> List[TimeSeriesMetric]:
        """Track skill accumulation over time."""
        if not achievements:
            return []
            
        result = []
        skills_accumulated = set()
        
        for a in achievements:
            if a.skills_demonstrated:
                before_count = len(skills_accumulated)
                skills_accumulated.update(a.skills_demonstrated)
                after_count = len(skills_accumulated)
                
                if after_count > before_count:
                    result.append(TimeSeriesMetric(
                        timestamp=a.completed_at,
                        value=after_count,
                        label=f"Added {after_count - before_count} new skills"
                    ))
                    
        return result
    
    def _calculate_category_distribution(
        self, 
        achievements: List[Achievement]
    ) -> Dict[str, int]:
        """Calculate achievement distribution by category."""
        distribution = {}
        for a in achievements:
            distribution[a.category] = distribution.get(a.category, 0) + 1
        return distribution
    
    def _generate_skill_radar(
        self, 
        achievements: List[Achievement]
    ) -> List[SkillRadarData]:
        """Generate skill radar chart data."""
        # Aggregate skill data
        skill_scores = {}
        skill_counts = {}
        
        for a in achievements:
            if not a.skills_demonstrated:
                continue
                
            for skill in a.skills_demonstrated:
                if skill not in skill_scores:
                    skill_scores[skill] = []
                    skill_counts[skill] = 0
                    
                skill_scores[skill].append(a.complexity_score or 50)
                skill_counts[skill] += 1
        
        # Calculate radar data
        radar_data = []
        for skill, scores in skill_scores.items():
            current_level = np.mean(scores) / 10  # Convert to 0-10 scale
            
            # Calculate growth trend
            if len(scores) > 1:
                first_half_avg = np.mean(scores[:len(scores)//2])
                second_half_avg = np.mean(scores[len(scores)//2:])
                growth_trend = (second_half_avg - first_half_avg) / max(first_half_avg, 1)
            else:
                growth_trend = 0
                
            radar_data.append(SkillRadarData(
                skill=skill,
                current_level=round(current_level, 1),
                industry_average=5.0,  # Placeholder
                growth_trend=round(max(-1, min(1, growth_trend)), 2)
            ))
            
        # Return top 12 skills by level
        return sorted(radar_data, key=lambda x: x.current_level, reverse=True)[:12]
    
    def _generate_impact_heatmap(
        self, 
        achievements: List[Achievement]
    ) -> List[ImpactHeatmap]:
        """Generate weekly impact heatmap data."""
        if not achievements:
            return []
            
        # Group by week and category
        heatmap_data = {}
        
        for a in achievements:
            week_key = a.completed_at.strftime('%Y-W%U')
            category = a.category
            key = (week_key, category)
            
            if key not in heatmap_data:
                heatmap_data[key] = {
                    'impact_total': 0,
                    'count': 0
                }
                
            heatmap_data[key]['impact_total'] += a.impact_score or 0
            heatmap_data[key]['count'] += 1
        
        # Convert to heatmap format
        result = []
        for (week, category), data in heatmap_data.items():
            result.append(ImpactHeatmap(
                week=week,
                category=category,
                impact_score=round(data['impact_total'] / max(data['count'], 1), 1),
                count=data['count']
            ))
            
        return sorted(result, key=lambda x: x.week)
    
    def _identify_career_milestones(
        self, 
        achievements: List[Achievement]
    ) -> List[CareerMilestone]:
        """Identify significant career milestones."""
        milestones = []
        
        # High impact achievements
        for a in achievements:
            if (a.impact_score or 0) >= 80:
                milestones.append(CareerMilestone(
                    date=a.completed_at,
                    title=a.title,
                    description=a.description or "",
                    impact="high" if a.impact_score < 90 else "critical",
                    category=a.category
                ))
        
        # First achievement in each category
        seen_categories = set()
        for a in achievements:
            if a.category not in seen_categories:
                seen_categories.add(a.category)
                milestones.append(CareerMilestone(
                    date=a.completed_at,
                    title=f"First {a.category} achievement",
                    description=a.title,
                    impact="medium",
                    category=a.category
                ))
        
        # Skills milestones (every 5 new skills)
        skills_accumulated = set()
        skill_milestones = [5, 10, 20, 30, 50]
        
        for a in achievements:
            if a.skills_demonstrated:
                before_count = len(skills_accumulated)
                skills_accumulated.update(a.skills_demonstrated)
                after_count = len(skills_accumulated)
                
                for milestone in skill_milestones:
                    if before_count < milestone <= after_count:
                        milestones.append(CareerMilestone(
                            date=a.completed_at,
                            title=f"Reached {milestone} skills",
                            description=f"Demonstrated proficiency in {milestone} different skills",
                            impact="high",
                            category="skills"
                        ))
        
        return sorted(milestones, key=lambda x: x.date)
    
    def _calculate_percentile_rank(self, achievements: List[Achievement]) -> int:
        """Calculate percentile rank based on achievements."""
        if not achievements:
            return 0
            
        # Simple calculation based on achievement rate and impact
        monthly_rate = len(achievements) / max(
            (achievements[-1].completed_at - achievements[0].completed_at).days / 30, 1
        )
        avg_impact = self._calculate_average_impact(achievements)
        
        # Scoring formula
        score = monthly_rate * 10 + avg_impact
        
        # Convert to percentile (simplified)
        if score >= 100:
            return 95
        elif score >= 75:
            return 85
        elif score >= 50:
            return 70
        elif score >= 30:
            return 50
        else:
            return 30
    
    def _calculate_improvement_rate(self, achievements: List[Achievement]) -> float:
        """Calculate rate of improvement over time."""
        if len(achievements) < 4:
            return 0.0
            
        # Compare first quarter to last quarter
        quarter_size = len(achievements) // 4
        first_quarter = achievements[:quarter_size]
        last_quarter = achievements[-quarter_size:]
        
        first_avg_impact = np.mean([
            a.impact_score for a in first_quarter if a.impact_score
        ]) if first_quarter else 0
        
        last_avg_impact = np.mean([
            a.impact_score for a in last_quarter if a.impact_score
        ]) if last_quarter else 0
        
        if first_avg_impact == 0:
            return 0.0
            
        improvement = (last_avg_impact - first_avg_impact) / first_avg_impact * 100
        return round(improvement, 1)
    
    def _calculate_momentum_score(self, achievements: List[Achievement]) -> float:
        """Calculate current momentum score (0-100)."""
        if not achievements:
            return 0.0
            
        # Recent achievements (last 30 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_achievements = [
            a for a in achievements if a.completed_at >= recent_cutoff
        ]
        
        if not recent_achievements:
            return 0.0
            
        # Factors for momentum
        recency_factor = len(recent_achievements) * 10  # Max 50
        impact_factor = np.mean([
            a.impact_score for a in recent_achievements if a.impact_score
        ]) * 0.5 if recent_achievements else 0  # Max 50
        
        momentum = min(recency_factor + impact_factor, 100)
        return round(momentum, 1)
    
    def generate_executive_summary(
        self,
        db: Session,
        user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate executive summary of career achievements.
        
        Args:
            db: Database session
            user_id: Optional user filter
            
        Returns:
            Executive summary data
        """
        # Get all achievements
        query = db.query(Achievement)
        if user_id:
            query = query.filter(Achievement.user_id == user_id)
        achievements = query.order_by(Achievement.completed_at.desc()).all()
        
        if not achievements:
            return {
                'status': 'No achievements found',
                'recommendations': ['Start tracking your achievements']
            }
        
        # Calculate key metrics
        total_impact = sum(a.impact_score or 0 for a in achievements)
        avg_complexity = np.mean([
            a.complexity_score for a in achievements if a.complexity_score
        ]) if achievements else 0
        
        # Top achievements
        top_achievements = sorted(
            achievements, 
            key=lambda a: a.impact_score or 0, 
            reverse=True
        )[:3]
        
        # Career progression
        first_date = achievements[-1].completed_at
        last_date = achievements[0].completed_at
        career_span_years = (last_date - first_date).days / 365
        
        return {
            'overview': {
                'total_achievements': len(achievements),
                'career_span_years': round(career_span_years, 1),
                'total_impact_score': round(total_impact, 0),
                'average_complexity': round(avg_complexity, 1)
            },
            'highlights': [
                {
                    'title': a.title,
                    'impact': a.impact_score,
                    'date': a.completed_at.strftime('%Y-%m-%d')
                }
                for a in top_achievements
            ],
            'growth_metrics': {
                'skill_count': self._count_unique_skills(achievements),
                'category_breadth': len(set(a.category for a in achievements)),
                'momentum_score': self._calculate_momentum_score(achievements)
            },
            'recommendations': self._generate_executive_recommendations(achievements)
        }
    
    def _generate_executive_recommendations(
        self, 
        achievements: List[Achievement]
    ) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []
        
        # Check achievement frequency
        if len(achievements) > 0:
            days_span = (achievements[0].completed_at - achievements[-1].completed_at).days
            monthly_rate = len(achievements) / max(days_span / 30, 1)
            
            if monthly_rate < 2:
                recommendations.append(
                    "Increase achievement tracking frequency to better showcase progress"
                )
        
        # Check impact scores
        impact_scores = [a.impact_score for a in achievements if a.impact_score]
        if impact_scores and np.mean(impact_scores) < 60:
            recommendations.append(
                "Focus on high-impact projects to increase career value"
            )
        
        # Check skill diversity
        skill_count = self._count_unique_skills(achievements)
        if skill_count < 10:
            recommendations.append(
                "Expand skill set to increase market value and opportunities"
            )
        
        # Check recent activity
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        recent_count = sum(1 for a in achievements if a.completed_at >= recent_cutoff)
        if recent_count == 0:
            recommendations.append(
                "Resume achievement tracking to maintain career momentum"
            )
        
        return recommendations