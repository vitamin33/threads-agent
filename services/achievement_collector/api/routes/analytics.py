"""
Analytics API routes for advanced career insights.

Provides endpoints for career predictions, industry benchmarking,
and performance dashboards.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...analytics.career_predictor import CareerPredictor
from ...analytics.industry_benchmark import IndustryBenchmarker
from ...analytics.performance_dashboard import PerformanceDashboard
from ...db.config import get_db


class CompensationBenchmarkRequest(BaseModel):
    """Request model for compensation benchmarking."""
    role: str
    years_experience: float
    skills: List[str]
    location: str = "Remote"
    achievements_count: int = 0


class SkillMarketAnalysisRequest(BaseModel):
    """Request model for skill market analysis."""
    skills: List[str]

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Initialize analytics engines
career_predictor = CareerPredictor()
industry_benchmarker = IndustryBenchmarker()
performance_dashboard = PerformanceDashboard()


@router.get("/career-prediction")
async def predict_career_trajectory(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_horizon_months: int = Query(24, description="Prediction horizon in months")
):
    """
    Predict career trajectory based on achievement history.
    
    Returns AI-powered predictions for next career moves including:
    - Potential next roles with confidence scores
    - Required skills for advancement
    - Timeline estimates
    - Salary projections
    """
    try:
        predictions = await career_predictor.predict_career_trajectory(
            db, user_id, time_horizon_months
        )
        return {
            "predictions": [p.dict() for p in predictions],
            "generated_at": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skill-gap-analysis")
async def analyze_skill_gaps(
    target_role: str = Query(..., description="Target job role"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Analyze skill gaps for a target role.
    
    Compares current skills against requirements for the target role
    and provides recommendations for closing gaps.
    """
    try:
        analysis = await career_predictor.analyze_skill_gaps(
            db, target_role, user_id
        )
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/industry-benchmark")
async def get_industry_benchmarks(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_period_days: int = Query(365, description="Period to analyze")
):
    """
    Benchmark achievements against industry standards.
    
    Compares your metrics against industry averages and top performers,
    providing percentile rankings and improvement recommendations.
    """
    try:
        benchmarks = industry_benchmarker.benchmark_achievements(
            db, user_id, time_period_days
        )
        return {
            "benchmarks": [b.dict() for b in benchmarks],
            "period_days": time_period_days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compensation-benchmark")
async def benchmark_compensation(request: CompensationBenchmarkRequest):
    """
    Benchmark compensation based on role, experience, and achievements.
    
    Provides salary estimates and market positioning based on:
    - Job role and experience level
    - Skill premiums
    - Geographic location
    - Achievement track record
    """
    try:
        benchmark = await industry_benchmarker.benchmark_compensation(
            request.role, 
            request.years_experience, 
            request.skills, 
            request.location, 
            request.achievements_count
        )
        return benchmark.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skill-market-analysis")
async def analyze_skill_market(request: SkillMarketAnalysisRequest):
    """
    Analyze market conditions for specific skills.
    
    Provides market data including:
    - Demand vs supply ratios
    - Average salary premiums
    - Job posting counts
    - Growth trends and future outlook
    """
    try:
        market_data = industry_benchmarker.analyze_skill_market(request.skills)
        return {
            "skills": [s.dict() for s in market_data],
            "analysis_date": "2024-01-01"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard-metrics")
async def get_dashboard_metrics(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    time_period_days: int = Query(365, description="Period to analyze")
):
    """
    Get comprehensive dashboard metrics for visualization.
    
    Returns complete analytics package including:
    - Time series data for achievements and impact
    - Skill progression and radar chart data
    - Impact heatmaps and category distributions
    - Career milestones and momentum scores
    """
    try:
        metrics = performance_dashboard.generate_dashboard_metrics(
            db, user_id, time_period_days
        )
        return metrics.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/executive-summary")
async def get_executive_summary(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Generate executive summary of career achievements.
    
    Provides high-level overview suitable for:
    - Performance reviews
    - Career planning discussions
    - Resume summaries
    - LinkedIn profile optimization
    """
    try:
        summary = performance_dashboard.generate_executive_summary(db, user_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/career-insights")
async def get_career_insights(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Get comprehensive career insights combining all analytics.
    
    Aggregates data from multiple analytics engines to provide
    a complete picture of career status and trajectory.
    """
    try:
        # Get various analytics
        predictions = await career_predictor.predict_career_trajectory(db, user_id, 12)
        benchmarks = industry_benchmarker.benchmark_achievements(db, user_id, 365)
        summary = performance_dashboard.generate_executive_summary(db, user_id)
        
        # Find top benchmark metric
        top_percentile = max(
            (b.percentile for b in benchmarks), 
            default=50
        )
        
        return {
            "current_status": {
                "level": summary.get("overview", {}).get("total_achievements", 0),
                "market_position": f"Top {100 - top_percentile}%",
                "momentum": summary.get("growth_metrics", {}).get("momentum_score", 0)
            },
            "next_moves": [
                {
                    "role": p.next_role,
                    "timeline": f"{p.timeline_months} months",
                    "confidence": f"{p.confidence * 100:.0f}%"
                }
                for p in predictions[:2]
            ],
            "key_strengths": benchmarks[:3] if benchmarks else [],
            "recommendations": summary.get("recommendations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trending-skills")
async def get_trending_skills():
    """
    Get list of currently trending skills in the market.
    
    Returns skills with high demand, growth rates, and
    recommendations for skill development priorities.
    """
    # Curated list of trending skills
    trending_skills = [
        "AI/ML", "GenAI", "LLM", "Kubernetes", "Cloud Architecture",
        "DevOps", "Data Engineering", "Cybersecurity", "Blockchain",
        "Edge Computing", "Quantum Computing", "WebAssembly"
    ]
    
    try:
        market_data = industry_benchmarker.analyze_skill_market(trending_skills)
        
        # Sort by market ratio (demand/supply)
        sorted_skills = sorted(
            market_data, 
            key=lambda s: s.market_ratio, 
            reverse=True
        )
        
        return {
            "trending_skills": [s.dict() for s in sorted_skills],
            "recommendations": [
                f"Focus on {sorted_skills[0].skill_name} - highest demand/supply ratio",
                f"Consider {sorted_skills[1].skill_name} - strong growth potential",
                "Combine trending skills with domain expertise for maximum value"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))