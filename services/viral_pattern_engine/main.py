"""FastAPI service for viral pattern extraction."""

from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor


app = FastAPI(
    title="Viral Pattern Engine",
    description="AI-powered viral content pattern extraction service",
    version="1.0.0",
)

# Initialize pattern extractor
pattern_extractor = ViralPatternExtractor()


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""

    posts: List[ViralPost]


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis."""

    results: List[Dict[str, Any]]
    summary: Dict[str, Any]


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "viral_pattern_engine"}


@app.post("/extract-patterns")
async def extract_patterns(post: ViralPost) -> Dict[str, Any]:
    """
    Extract viral patterns from a single post.

    Args:
        post: ViralPost to analyze

    Returns:
        Dictionary containing extracted patterns
    """
    try:
        patterns = pattern_extractor.extract_patterns(post)
        return patterns
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Pattern extraction failed: {str(e)}"
        )


@app.post("/analyze-batch")
async def analyze_batch(request: BatchAnalysisRequest) -> BatchAnalysisResponse:
    """
    Analyze multiple posts in batch.

    Args:
        request: Batch analysis request containing list of posts

    Returns:
        BatchAnalysisResponse with results and summary
    """
    try:
        results = []
        total_pattern_strength = 0.0

        for post in request.posts:
            patterns = pattern_extractor.extract_patterns(post)
            results.append(patterns)
            total_pattern_strength += patterns.get("pattern_strength", 0.0)

        # Calculate summary statistics
        summary = {
            "total_posts": len(request.posts),
            "average_pattern_strength": total_pattern_strength / len(request.posts)
            if request.posts
            else 0.0,
            "total_hook_patterns": sum(
                len(r.get("hook_patterns", [])) for r in results
            ),
            "total_emotion_patterns": sum(
                len(r.get("emotion_patterns", [])) for r in results
            ),
        }

        return BatchAnalysisResponse(results=results, summary=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@app.get("/pattern-types")
async def get_pattern_types() -> Dict[str, List[str]]:
    """
    Get available pattern types that can be detected.

    Returns:
        Dictionary of pattern categories and their types
    """
    return {
        "hook_patterns": [
            "discovery",
            "statistical",
            "transformation_story",
            "curiosity_gap",
            "urgency",
        ],
        "emotion_patterns": ["excitement", "amazement", "surprise"],
        "structure_patterns": ["short", "medium", "long"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
