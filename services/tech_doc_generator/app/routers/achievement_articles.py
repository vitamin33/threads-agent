"""
Achievement-based Article Generation Routes

Endpoints for generating articles from achievements stored in the 
achievement_collector service.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import structlog

from ..models.article import (
    ArticleType, 
    Platform, 
    Article, 
    ArticleStatus,
    ArticleContent
)
from ..services.achievement_content_generator import AchievementContentGenerator
from ..services.insight_predictor import InsightPredictor

logger = structlog.get_logger()
router = APIRouter(prefix="/achievement-articles", tags=["achievement-integration"])

# Service instances
achievement_generator = AchievementContentGenerator()
insight_predictor = InsightPredictor()


class AchievementArticleRequest(BaseModel):
    """Request model for achievement-based article generation"""
    achievement_id: int
    article_types: List[ArticleType] = [ArticleType.CASE_STUDY, ArticleType.LESSONS_LEARNED]
    platforms: List[Platform] = [Platform.LINKEDIN, Platform.DEVTO]
    auto_publish: bool = False


class WeeklyHighlightsRequest(BaseModel):
    """Request model for weekly highlights generation"""
    platforms: List[Platform] = [Platform.LINKEDIN, Platform.MEDIUM]
    auto_publish: bool = True


class CompanyContentRequest(BaseModel):
    """Request model for company-specific content"""
    company_name: str
    categories: Optional[List[str]] = None
    auto_publish: bool = False


@router.post("/generate-from-achievement", response_model=List[Article])
async def generate_from_achievement(
    request: AchievementArticleRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate articles from a specific achievement.
    
    This endpoint integrates with the achievement_collector service to
    create multiple article variations from your professional achievements.
    """
    try:
        logger.info("generating_articles_from_achievement",
                   achievement_id=request.achievement_id,
                   article_types=request.article_types,
                   platforms=request.platforms)
                   
        # Generate content variations
        content_list = await achievement_generator.generate_from_achievement(
            request.achievement_id,
            request.article_types,
            request.platforms
        )
        
        if not content_list:
            raise HTTPException(
                status_code=404,
                detail=f"Achievement {request.achievement_id} not found or no content generated"
            )
            
        # Create article records with quality scores
        articles = []
        for content in content_list:
            # Predict insight quality
            score = await insight_predictor.predict_insight_quality(
                content, 
                {"type": "achievement", "id": request.achievement_id},
                content.platform
            )
            
            article = Article(
                id=f"ach_{request.achievement_id}_{content.platform.value}_{content.article_type.value}",
                request=None,  # No traditional request
                status=ArticleStatus.DRAFT,
                content=content,
                insight_score=score,
                analysis=content.metadata
            )
            articles.append(article)
            
        # Sort by insight score
        articles.sort(key=lambda x: x.insight_score.overall_score, reverse=True)
        
        # Auto-publish if requested and quality is high
        if request.auto_publish and articles[0].insight_score.overall_score >= 7.5:
            logger.info("auto_publishing_top_article",
                       article_id=articles[0].id,
                       score=articles[0].insight_score.overall_score)
            # Add publishing task here
            
        return articles
        
    except Exception as e:
        logger.error("achievement_article_generation_failed",
                    achievement_id=request.achievement_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-weekly-highlights", response_model=List[Article])
async def generate_weekly_highlights(
    request: WeeklyHighlightsRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate articles from the week's top achievements.
    
    Perfect for maintaining consistent content presence by automatically
    creating content from your recent high-impact achievements.
    """
    try:
        logger.info("generating_weekly_highlights", platforms=request.platforms)
        
        content_list = await achievement_generator.generate_weekly_highlights(
            request.platforms
        )
        
        if not content_list:
            return []  # No recent achievements
            
        # Convert to articles
        articles = []
        for idx, content in enumerate(content_list):
            score = await insight_predictor.predict_insight_quality(
                content,
                {"type": "weekly_highlight", "index": idx},
                content.platform
            )
            
            article = Article(
                id=f"weekly_{datetime.now().strftime('%Y%m%d')}_{idx}",
                request=None,
                status=ArticleStatus.DRAFT,
                content=content,
                insight_score=score,
                analysis=content.metadata
            )
            articles.append(article)
            
        # Auto-publish high-quality content if requested
        if request.auto_publish:
            for article in articles:
                if article.insight_score.overall_score >= 7.0:
                    logger.info("scheduling_weekly_highlight",
                               article_id=article.id,
                               platform=article.content.platform)
                    # Add to publishing queue
                    
        return articles
        
    except Exception as e:
        logger.error("weekly_highlights_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-company-content", response_model=List[Article])
async def generate_company_content(request: CompanyContentRequest):
    """
    Generate content specifically targeted at a company.
    
    Creates articles that highlight achievements relevant to the target
    company's tech stack and challenges.
    """
    try:
        logger.info("generating_company_content",
                   company=request.company_name,
                   categories=request.categories)
                   
        content_list = await achievement_generator.generate_company_specific_content(
            request.company_name,
            request.categories
        )
        
        if not content_list:
            raise HTTPException(
                status_code=404,
                detail=f"No relevant achievements found for {request.company_name}"
            )
            
        # Convert to articles
        articles = []
        for content in content_list:
            score = await insight_predictor.predict_insight_quality(
                content,
                {"type": "company_targeted", "company": request.company_name},
                content.platform
            )
            
            # Boost score for company relevance
            score.overall_score = min(10.0, score.overall_score * 1.1)
            
            article = Article(
                id=f"company_{request.company_name}_{content.platform.value}_{len(articles)}",
                request=None,
                status=ArticleStatus.DRAFT,
                content=content,
                insight_score=score,
                analysis=content.metadata
            )
            articles.append(article)
            
        return articles
        
    except Exception as e:
        logger.error("company_content_failed",
                    company=request.company_name,
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/achievement/{achievement_id}/potential-articles")
async def preview_potential_articles(achievement_id: int):
    """
    Preview what articles could be generated from an achievement.
    
    Useful for understanding the content potential of an achievement
    before generating actual articles.
    """
    try:
        # Get achievement details
        async with achievement_generator.achievement_client as client:
            achievement = await client.get_achievement(achievement_id)
            
        if not achievement:
            raise HTTPException(status_code=404, detail="Achievement not found")
            
        # Suggest article types based on achievement characteristics
        suggestions = []
        
        if achievement.impact_score >= 85:
            suggestions.append({
                "article_type": ArticleType.CASE_STUDY,
                "platforms": [Platform.LINKEDIN, Platform.MEDIUM],
                "reason": "High impact score makes this perfect for a detailed case study"
            })
            
        if achievement.technical_details:
            suggestions.append({
                "article_type": ArticleType.TECHNICAL_DEEP_DIVE,
                "platforms": [Platform.DEVTO, Platform.GITHUB],
                "reason": "Rich technical details available for deep dive"
            })
            
        if achievement.business_value:
            suggestions.append({
                "article_type": ArticleType.LESSONS_LEARNED,
                "platforms": [Platform.LINKEDIN],
                "reason": "Clear business value for professional audience"
            })
            
        return {
            "achievement": {
                "id": achievement.id,
                "title": achievement.title,
                "impact_score": achievement.impact_score,
                "category": achievement.category
            },
            "potential_articles": suggestions,
            "estimated_articles": len(suggestions) * 2  # For multiple platforms
        }
        
    except Exception as e:
        logger.error("preview_failed", achievement_id=achievement_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))