from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
import uuid
import structlog

from ..models.article import (
    ArticleRequest, Article, ArticleContent, ArticleStatus, 
    InsightScore, PublishRequest, PredictionRequest
)
from ..services.code_analyzer import CodeAnalyzer
from ..services.content_generator import ContentGenerator
from ..services.insight_predictor import InsightPredictor
from ..services.platform_publisher import PlatformPublisher, PublishingScheduler
from ..core.config import get_settings

logger = structlog.get_logger()
router = APIRouter()

# Global service instances (would use dependency injection in production)
settings = get_settings()
code_analyzer = CodeAnalyzer(settings.repo_path)
content_generator = ContentGenerator()
insight_predictor = InsightPredictor()
platform_publisher = PlatformPublisher()
publishing_scheduler = PublishingScheduler()

# In-memory storage (would use database in production)
articles_db = {}

@router.post("/generate", response_model=Article)
async def generate_article(request: ArticleRequest, background_tasks: BackgroundTasks):
    """Generate a new article from code analysis"""
    
    try:
        logger.info("Generating article", source_type=request.source_type, source_path=request.source_path)
        
        # Create article record
        article_id = str(uuid.uuid4())
        article = Article(
            id=article_id,
            request=request,
            status=ArticleStatus.DRAFT
        )
        
        # Analyze code
        analysis = await code_analyzer.analyze_source(request.source_type, request.source_path)
        article.analysis = analysis
        
        # Generate content for each requested angle and platform
        best_content = None
        best_score = 0
        
        for article_type in request.angles:
            for platform in request.target_platforms:
                content = await content_generator.generate_article(
                    analysis, article_type, platform
                )
                
                # Predict quality
                score = await insight_predictor.predict_insight_quality(
                    content, analysis, platform
                )
                
                if score.overall_score > best_score:
                    best_content = content
                    best_score = score.overall_score
                    article.insight_score = score
        
        article.content = best_content
        articles_db[article_id] = article
        
        # Auto-publish if requested
        if request.auto_publish and best_score >= settings.min_insight_score:
            background_tasks.add_task(
                auto_publish_article, 
                article_id, 
                request.target_platforms
            )
        
        logger.info("Article generated", 
                   article_id=article_id, 
                   insight_score=best_score,
                   auto_publish=request.auto_publish)
        
        return article
        
    except Exception as e:
        logger.error("Article generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Article generation failed: {str(e)}")

@router.get("/", response_model=List[Article])
async def list_articles(status: Optional[ArticleStatus] = None, limit: int = 10):
    """List generated articles"""
    
    articles = list(articles_db.values())
    
    if status:
        articles = [a for a in articles if a.status == status]
    
    # Sort by creation date, most recent first
    articles.sort(key=lambda x: x.created_at, reverse=True)
    
    return articles[:limit]

@router.get("/{article_id}", response_model=Article)
async def get_article(article_id: str):
    """Get specific article by ID"""
    
    if article_id not in articles_db:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return articles_db[article_id]

@router.post("/{article_id}/publish")
async def publish_article(article_id: str, publish_request: PublishRequest):
    """Publish article to specified platforms"""
    
    if article_id not in articles_db:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = articles_db[article_id]
    
    if not article.content:
        raise HTTPException(status_code=400, detail="Article has no content to publish")
    
    try:
        results = {}
        
        for platform in publish_request.platforms:
            custom_content = publish_request.custom_content.get(platform) if publish_request.custom_content else None
            
            result = await platform_publisher.publish_to_platform(
                platform, article.content, custom_content
            )
            
            results[platform.value] = result
            
            if result.get('success') and result.get('url'):
                article.published_urls[platform] = result['url']
        
        # Update article status
        if any(r.get('success') for r in results.values()):
            article.status = ArticleStatus.PUBLISHED
        else:
            article.status = ArticleStatus.FAILED
        
        articles_db[article_id] = article
        
        logger.info("Article publish attempt completed", 
                   article_id=article_id, 
                   results=results)
        
        return {
            "article_id": article_id,
            "results": results,
            "status": article.status
        }
        
    except Exception as e:
        logger.error("Article publishing failed", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Publishing failed: {str(e)}")

@router.post("/{article_id}/schedule")
async def schedule_article(article_id: str, schedule_request: dict):
    """Schedule article publication"""
    
    if article_id not in articles_db:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = articles_db[article_id]
    
    try:
        # Get optimal times if not specified
        platforms = schedule_request.get('platforms', [])
        schedule_times = schedule_request.get('schedule_times', {})
        
        if not schedule_times:
            schedule_times = publishing_scheduler.get_optimal_posting_times(platforms)
        
        result = await publishing_scheduler.schedule_publication(
            article_id, platforms, schedule_times
        )
        
        article.status = ArticleStatus.SCHEDULED
        articles_db[article_id] = article
        
        return result
        
    except Exception as e:
        logger.error("Article scheduling failed", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Scheduling failed: {str(e)}")

@router.post("/predict-quality", response_model=InsightScore)
async def predict_article_quality(request: PredictionRequest):
    """Predict quality of article content"""
    
    try:
        # Create temporary content object
        content = ArticleContent(
            title=request.title,
            content=request.content,
            tags=request.tags
        )
        
        score = await insight_predictor.predict_insight_quality(
            content, None, request.target_platform
        )
        
        return score
        
    except Exception as e:
        logger.error("Quality prediction failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/{article_id}/suggestions")
async def get_improvement_suggestions(article_id: str):
    """Get suggestions to improve article quality"""
    
    if article_id not in articles_db:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = articles_db[article_id]
    
    if not article.content or not article.insight_score:
        raise HTTPException(status_code=400, detail="Article needs content and quality score")
    
    try:
        suggestions = await insight_predictor.get_improvement_suggestions(
            article.content, article.insight_score
        )
        
        return {
            "article_id": article_id,
            "current_score": article.insight_score.overall_score,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error("Suggestions generation failed", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")

@router.post("/{article_id}/feedback")
async def provide_feedback(article_id: str, feedback: dict):
    """Provide performance feedback to improve predictions"""
    
    if article_id not in articles_db:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = articles_db[article_id]
    
    if not article.insight_score:
        raise HTTPException(status_code=400, detail="Article has no prediction to update")
    
    try:
        await insight_predictor.update_model_with_feedback(
            article_id, article.insight_score, feedback
        )
        
        # Store performance metrics
        article.performance_metrics.update(feedback)
        articles_db[article_id] = article
        
        return {"message": "Feedback recorded successfully"}
        
    except Exception as e:
        logger.error("Feedback recording failed", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Feedback failed: {str(e)}")

async def auto_publish_article(article_id: str, platforms: List):
    """Background task to auto-publish article"""
    
    try:
        if article_id not in articles_db:
            logger.error("Auto-publish failed: article not found", article_id=article_id)
            return
        
        article = articles_db[article_id]
        
        # Publish to each platform
        for platform in platforms:
            result = await platform_publisher.publish_to_platform(
                platform, article.content
            )
            
            if result.get('success') and result.get('url'):
                article.published_urls[platform] = result['url']
        
        article.status = ArticleStatus.PUBLISHED
        articles_db[article_id] = article
        
        logger.info("Auto-publish completed", 
                   article_id=article_id, 
                   platforms=[p.value for p in platforms])
        
    except Exception as e:
        logger.error("Auto-publish failed", article_id=article_id, error=str(e))