"""
Search-powered endpoints for Orchestrator
Provides trend detection and competitive analysis APIs
"""

import logging
import os
import sys
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.metrics import record_business_metric, record_http_request
from common.searxng_wrapper import analyze_viral, find_trends, search

logger = logging.getLogger(__name__)

# Create router for search endpoints
search_router = APIRouter(prefix="/search", tags=["search"])


class TrendSearchRequest(BaseModel):
    """Request for trend search"""

    topic: str
    timeframe: str = "week"  # day, week, month
    limit: int = 10


class CompetitiveAnalysisRequest(BaseModel):
    """Request for competitive analysis"""

    topic: str
    platform: str = "threads"
    analyze_patterns: bool = True


class EnhancedTaskRequest(BaseModel):
    """Enhanced task request with search"""

    persona_id: str
    topic: str
    enable_search: bool = True
    trend_timeframe: str = "day"


class SearchResponse(BaseModel):
    """Generic search response"""

    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]


@search_router.post("/trends")
async def search_trends(request: TrendSearchRequest) -> SearchResponse:
    """
    Find trending topics related to a base topic

    Example:
        POST /search/trends
        {
            "topic": "AI mental health",
            "timeframe": "week",
            "limit": 10
        }
    """
    with record_http_request("orchestrator", "POST", "/search/trends"):
        try:
            logger.info(f"Searching trends for topic: {request.topic}")

            # Find trends
            trends = find_trends(request.topic, request.timeframe)[: request.limit]

            # Record metrics
            record_business_metric(
                "trend_searches_total",
                1,
                {"topic": request.topic, "timeframe": request.timeframe},
            )

            return SearchResponse(
                success=True,
                data={
                    "trends": trends,
                    "topic": request.topic,
                    "timeframe": request.timeframe,
                },
                metadata={"count": len(trends), "source": "searxng"},
            )

        except Exception as e:
            logger.error(f"Trend search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@search_router.post("/competitive")
async def competitive_analysis(request: CompetitiveAnalysisRequest) -> SearchResponse:
    """
    Analyze viral content and competitor strategies

    Example:
        POST /search/competitive
        {
            "topic": "AI productivity tips",
            "platform": "threads",
            "analyze_patterns": true
        }
    """
    with record_http_request("orchestrator", "POST", "/search/competitive"):
        try:
            logger.info(f"Analyzing competition for: {request.topic}")

            # Analyze viral content
            viral_patterns = analyze_viral(request.topic, request.platform)

            # Extract insights
            insights = {
                "viral_patterns": viral_patterns[:5],  # Top 5 patterns
                "common_keywords": _extract_common_keywords(viral_patterns),
                "hook_patterns": _extract_hook_patterns(viral_patterns),
                "engagement_indicators": _analyze_engagement_indicators(viral_patterns),
            }

            # Record metrics
            record_business_metric(
                "competitive_analyses_total",
                1,
                {"topic": request.topic, "platform": request.platform},
            )

            return SearchResponse(
                success=True,
                data=insights,
                metadata={
                    "patterns_found": len(viral_patterns),
                    "platform": request.platform,
                },
            )

        except Exception as e:
            logger.error(f"Competitive analysis failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@search_router.post("/quick")
async def quick_search(query: str, limit: int = 10) -> SearchResponse:
    """
    Quick search endpoint for general queries

    Example:
        POST /search/quick?query=AI%20trends%202025&limit=5
    """
    with record_http_request("orchestrator", "POST", "/search/quick"):
        try:
            logger.info(f"Quick search for: {query}")

            # Perform search
            results = search(query, limit=limit)

            # Convert to dict format
            results_dict = [r.to_dict() for r in results]

            return SearchResponse(
                success=True,
                data={"results": results_dict},
                metadata={"count": len(results), "query": query},
            )

        except Exception as e:
            logger.error(f"Quick search failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


@search_router.post("/enhanced-task")
async def create_enhanced_task(
    request: EnhancedTaskRequest, background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Create a search-enhanced content generation task

    This endpoint combines trend research and competitive analysis
    with the standard content generation pipeline.

    Example:
        POST /search/enhanced-task
        {
            "persona_id": "ai-jesus",
            "topic": "AI and spirituality",
            "enable_search": true,
            "trend_timeframe": "week"
        }
    """
    with record_http_request("orchestrator", "POST", "/search/enhanced-task"):
        try:
            task_id = str(uuid.uuid4())

            # Prepare enhanced task payload
            task_payload = {
                "persona_id": request.persona_id,
                "topic": request.topic,
                "search_enhanced": request.enable_search,
            }

            if request.enable_search:
                # Gather search context before queuing task
                logger.info(f"Gathering search context for task {task_id}")

                # Find trends
                trends = find_trends(request.topic, request.trend_timeframe)[:5]

                # Analyze viral content
                viral_patterns = analyze_viral(request.topic)[:3]

                # Add to task payload
                task_payload["search_context"] = {
                    "trends": trends,
                    "viral_patterns": viral_patterns,
                    "trending_keywords": [t["topic"] for t in trends[:3]],
                }

            # Queue the enhanced task
            # Note: This would integrate with your existing Celery task system
            # For now, we'll return the enhanced payload

            logger.info(f"Created enhanced task {task_id}")

            return {
                "task_id": task_id,
                "status": "queued",
                "search_enhanced": request.enable_search,
                "payload": task_payload,
            }

        except Exception as e:
            logger.error(f"Enhanced task creation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


# Helper functions
def _extract_common_keywords(patterns: List[Dict[str, Any]]) -> List[str]:
    """Extract common keywords from viral patterns"""
    keyword_counts = {}

    for pattern in patterns:
        keywords = pattern.get("keywords", [])
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

    # Sort by frequency
    sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    return [kw for kw, _ in sorted_keywords[:10]]


def _extract_hook_patterns(patterns: List[Dict[str, Any]]) -> List[str]:
    """Extract successful hook patterns"""
    hooks = []

    for pattern in patterns:
        title = pattern.get("title", "")
        # Look for question patterns
        if "?" in title:
            hooks.append("Question hook: " + title)
        # Look for number patterns
        elif any(char.isdigit() for char in title):
            hooks.append("Number hook: " + title)
        # Look for "How to" patterns
        elif title.lower().startswith(("how to", "why", "what")):
            hooks.append("How-to hook: " + title)

    return hooks[:5]  # Top 5 hook patterns


def _analyze_engagement_indicators(patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze what makes content engaging"""
    indicators = {
        "uses_questions": 0,
        "uses_numbers": 0,
        "uses_emotions": 0,
        "average_title_length": 0,
        "common_formats": [],
    }

    emotion_words = {
        "amazing",
        "incredible",
        "shocking",
        "surprising",
        "best",
        "worst",
        "love",
        "hate",
        "breakthrough",
        "revolutionary",
    }

    title_lengths = []

    for pattern in patterns:
        title = pattern.get("title", "").lower()

        if "?" in title:
            indicators["uses_questions"] += 1

        if any(char.isdigit() for char in title):
            indicators["uses_numbers"] += 1

        if any(word in title for word in emotion_words):
            indicators["uses_emotions"] += 1

        title_lengths.append(len(title.split()))

    if title_lengths:
        indicators["average_title_length"] = sum(title_lengths) / len(title_lengths)

    # Calculate percentages
    total = len(patterns) if patterns else 1
    indicators["uses_questions"] = round(indicators["uses_questions"] / total * 100, 1)
    indicators["uses_numbers"] = round(indicators["uses_numbers"] / total * 100, 1)
    indicators["uses_emotions"] = round(indicators["uses_emotions"] / total * 100, 1)

    return indicators
