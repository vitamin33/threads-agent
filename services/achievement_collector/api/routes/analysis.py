# Achievement Analysis Routes

from api.schemas import AnalysisRequest, AnalysisResponse
from core.config import settings
from core.logging import setup_logging
from db.config import get_db
from db.models import Achievement
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from services.ai_analyzer import AchievementAnalyzer

logger = setup_logging(__name__)
router = APIRouter()

# Initialize analyzer
analyzer = AchievementAnalyzer(api_key=settings.OPENAI_API_KEY)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_achievement(
    request: AnalysisRequest,
    db: Session = Depends(get_db),
):
    """Analyze achievement impact and generate insights"""

    # Get achievement
    achievement = (
        db.query(Achievement).filter(Achievement.id == request.achievement_id).first()
    )

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    try:
        # Run analysis
        analysis_result = await analyzer.analyze(
            achievement=achievement,
            analyze_impact=request.analyze_impact,
            analyze_technical=request.analyze_technical,
            generate_summary=request.generate_summary,
        )

        # Update achievement with analysis results
        achievement.impact_score = analysis_result.impact_score
        achievement.complexity_score = analysis_result.complexity_score
        achievement.business_value = analysis_result.business_value
        achievement.time_saved_hours = analysis_result.time_saved_hours

        if request.generate_summary:
            achievement.ai_summary = analysis_result.summary
        if request.analyze_impact:
            achievement.ai_impact_analysis = analysis_result.impact_analysis
        if request.analyze_technical:
            achievement.ai_technical_analysis = analysis_result.technical_analysis

        db.commit()

        logger.info(
            f"Analyzed achievement {achievement.id}: impact={analysis_result.impact_score}"
        )

        return analysis_result

    except Exception as e:
        logger.error(f"Analysis failed for achievement {request.achievement_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze_achievements(
    category: str = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Batch analyze multiple achievements"""

    # Get unanalyzed achievements
    query = db.query(Achievement).filter(Achievement.ai_summary.is_(None))

    if category:
        query = query.filter(Achievement.category == category)

    achievements = query.limit(limit).all()

    if not achievements:
        return {"message": "No achievements to analyze", "analyzed": 0}

    analyzed_count = 0
    errors = []

    for achievement in achievements:
        try:
            analysis_result = await analyzer.analyze(achievement=achievement)

            # Update achievement
            achievement.impact_score = analysis_result.impact_score
            achievement.complexity_score = analysis_result.complexity_score
            achievement.business_value = analysis_result.business_value
            achievement.time_saved_hours = analysis_result.time_saved_hours
            achievement.ai_summary = analysis_result.summary
            achievement.ai_impact_analysis = analysis_result.impact_analysis
            achievement.ai_technical_analysis = analysis_result.technical_analysis

            analyzed_count += 1

        except Exception as e:
            logger.error(f"Failed to analyze achievement {achievement.id}: {e}")
            errors.append({"achievement_id": achievement.id, "error": str(e)})

    db.commit()

    return {
        "analyzed": analyzed_count,
        "errors": errors,
        "message": f"Analyzed {analyzed_count} achievements",
    }


@router.get("/insights")
async def get_insights(
    db: Session = Depends(get_db),
):
    """Get AI-generated insights across all achievements"""

    # Get top achievements
    top_achievements = (
        db.query(Achievement)
        .filter(Achievement.portfolio_ready.is_(True))
        .order_by(Achievement.impact_score.desc())
        .limit(10)
        .all()
    )

    if not top_achievements:
        return {"message": "No achievements to analyze", "insights": []}

    try:
        insights = await analyzer.generate_portfolio_insights(top_achievements)

        return {
            "insights": insights,
            "achievement_count": len(top_achievements),
        }

    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=500, detail=f"Insight generation failed: {str(e)}"
        )
