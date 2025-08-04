"""FastAPI service for viral pattern extraction."""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper


app = FastAPI(
    title="Viral Pattern Engine",
    description="AI-powered viral content pattern extraction service",
    version="1.0.0",
)

# Initialize extractors and analyzers
pattern_extractor = ViralPatternExtractor()
emotion_analyzer = EmotionAnalyzer()
trajectory_mapper = TrajectoryMapper()


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""

    posts: List[ViralPost]


class BatchAnalysisResponse(BaseModel):
    """Response model for batch analysis."""

    results: List[Dict[str, Any]]
    summary: Dict[str, Any]


class EmotionAnalysisRequest(BaseModel):
    """Request model for emotion analysis."""
    
    text: str = Field(..., description="Text to analyze")
    segments: Optional[List[Dict[str, Any]]] = Field(None, description="Pre-segmented text pieces")


class EmotionTrajectoryRequest(BaseModel):
    """Request model for emotion trajectory analysis."""
    
    segments: List[Dict[str, Any]] = Field(..., description="List of content segments")
    persona_id: Optional[str] = Field(None, description="Persona ID for tracking")


class EmotionTemplateRequest(BaseModel):
    """Request model for creating emotion template."""
    
    name: str = Field(..., description="Template name")
    trajectory_type: str = Field(..., description="Type of emotional trajectory")
    emotion_sequence: List[str] = Field(..., description="Sequence of emotions")
    description: Optional[str] = Field(None, description="Template description")


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


# Emotion Analysis Endpoints

@app.post("/analyze/emotion")
async def analyze_emotion(request: EmotionAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze emotions in text content.
    
    Args:
        request: EmotionAnalysisRequest with text to analyze
        
    Returns:
        Dictionary containing emotion analysis results
    """
    try:
        result = emotion_analyzer.analyze_emotion(request.text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Emotion analysis failed: {str(e)}"
        )


@app.post("/analyze/emotion-trajectory")
async def analyze_emotion_trajectory(request: EmotionTrajectoryRequest) -> Dict[str, Any]:
    """
    Analyze emotion trajectory across content segments.
    
    Args:
        request: EmotionTrajectoryRequest with segments to analyze
        
    Returns:
        Dictionary containing trajectory analysis
    """
    try:
        # Analyze emotions in each segment if not already analyzed
        analyzed_segments = []
        for segment in request.segments:
            if "emotions" not in segment:
                text = segment.get("text", "")
                emotion_result = emotion_analyzer.analyze_emotion(text)
                segment["emotions"] = emotion_result["emotions"]
            analyzed_segments.append(segment)
        
        # Map trajectory
        trajectory = trajectory_mapper.map_emotion_trajectory(analyzed_segments)
        
        # Add metadata
        if request.persona_id:
            trajectory["persona_id"] = request.persona_id
            
        return trajectory
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Trajectory analysis failed: {str(e)}"
        )


@app.post("/analyze/emotion-transitions")
async def analyze_emotion_transitions(request: EmotionTrajectoryRequest) -> Dict[str, Any]:
    """
    Analyze emotion transitions between segments.
    
    Args:
        request: EmotionTrajectoryRequest with segments
        
    Returns:
        Dictionary containing transition analysis
    """
    try:
        transitions = []
        
        for i in range(len(request.segments) - 1):
            current = request.segments[i]
            next_seg = request.segments[i + 1]
            
            # Ensure emotions are analyzed
            if "emotions" not in current:
                current["emotions"] = emotion_analyzer.analyze_emotion(
                    current.get("text", "")
                )["emotions"]
            if "emotions" not in next_seg:
                next_seg["emotions"] = emotion_analyzer.analyze_emotion(
                    next_seg.get("text", "")
                )["emotions"]
            
            # Get dominant emotions
            current_dominant = max(current["emotions"], key=current["emotions"].get)
            next_dominant = max(next_seg["emotions"], key=next_seg["emotions"].get)
            
            transitions.append({
                "from_segment": i,
                "to_segment": i + 1,
                "from_emotion": current_dominant,
                "to_emotion": next_dominant,
                "intensity_change": next_seg["emotions"][next_dominant] - current["emotions"][current_dominant]
            })
        
        return {
            "transitions": transitions,
            "total_segments": len(request.segments),
            "persona_id": request.persona_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Transition analysis failed: {str(e)}"
        )


@app.post("/templates/emotion", status_code=201)
async def create_emotion_template(request: EmotionTemplateRequest) -> Dict[str, Any]:
    """
    Create a new emotion template.
    
    Args:
        request: EmotionTemplateRequest with template details
        
    Returns:
        Created template information
    """
    try:
        # In a real implementation, this would save to database
        template = {
            "template_id": hash(request.name) % 100000,  # Simple ID generation
            "name": request.name,
            "trajectory_type": request.trajectory_type,
            "emotion_sequence": request.emotion_sequence,
            "description": request.description,
            "created_at": "2024-01-01T00:00:00Z",
            "is_active": True,
            "effectiveness_score": 0.0,
            "usage_count": 0
        }
        
        return template
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Template creation failed: {str(e)}"
        )


@app.get("/templates/emotion")
async def get_emotion_templates(
    min_effectiveness: Optional[float] = None,
    is_active: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get emotion templates filtered by effectiveness.
    
    Args:
        min_effectiveness: Minimum effectiveness score
        is_active: Filter by active status
        
    Returns:
        List of templates
    """
    # Mock templates for now
    templates = [
        {
            "template_id": 1,
            "name": "Rising Hope",
            "trajectory_type": "rising",
            "effectiveness_score": 0.85,
            "is_active": True
        },
        {
            "template_id": 2,
            "name": "Emotional Rollercoaster",
            "trajectory_type": "volatile",
            "effectiveness_score": 0.72,
            "is_active": True
        }
    ]
    
    # Apply filters
    if min_effectiveness:
        templates = [t for t in templates if t["effectiveness_score"] >= min_effectiveness]
    if is_active is not None:
        templates = [t for t in templates if t["is_active"] == is_active]
    
    return templates


@app.get("/trajectories/emotion/{trajectory_id}")
async def get_emotion_trajectory_by_id(trajectory_id: int) -> Dict[str, Any]:
    """
    Get emotion trajectory by ID.
    
    Args:
        trajectory_id: Trajectory ID
        
    Returns:
        Trajectory details
    """
    # Mock response for now
    return {
        "trajectory_id": trajectory_id,
        "arc_type": "rising",
        "segments": [],
        "transitions": [],
        "metrics": {
            "volatility": 0.3,
            "consistency": 0.7,
            "peak_intensity": 0.9
        }
    }


@app.get("/trajectories/emotion/persona/{persona_id}")
async def get_emotion_trajectories_by_persona(persona_id: str) -> List[Dict[str, Any]]:
    """
    Get all emotion trajectories for a persona.
    
    Args:
        persona_id: Persona ID
        
    Returns:
        List of trajectories
    """
    # Mock response
    return [
        {
            "trajectory_id": 1,
            "persona_id": persona_id,
            "arc_type": "rising",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]


@app.post("/batch/emotion-analysis")
async def batch_emotion_analysis(texts: List[str]) -> Dict[str, Any]:
    """
    Analyze emotions in multiple texts.
    
    Args:
        texts: List of texts to analyze
        
    Returns:
        Batch analysis results
    """
    try:
        results = []
        total_time = 0
        
        for text in texts:
            import time
            start = time.time()
            result = emotion_analyzer.analyze_emotion(text)
            elapsed = (time.time() - start) * 1000  # ms
            
            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "emotions": result["emotions"],
                "dominant_emotion": result["dominant_emotion"],
                "processing_time_ms": elapsed
            })
            total_time += elapsed
        
        return {
            "results": results,
            "total_texts": len(texts),
            "total_processing_time_ms": total_time,
            "average_time_per_text_ms": total_time / len(texts) if texts else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch analysis failed: {str(e)}"
        )


@app.put("/templates/emotion/{template_id}/performance")
async def update_template_performance(
    template_id: int,
    engagement_rate: float,
    views: int
) -> Dict[str, Any]:
    """
    Update template performance metrics.
    
    Args:
        template_id: Template ID
        engagement_rate: Engagement rate
        views: Number of views
        
    Returns:
        Updated template
    """
    # Mock update
    return {
        "template_id": template_id,
        "effectiveness_score": min(engagement_rate * 10, 1.0),  # Simple calculation
        "usage_count": views,
        "updated_at": "2024-01-01T00:00:00Z"
    }


@app.post("/analyze/content-emotion-workflow")
async def analyze_content_emotion_workflow(content: str) -> Dict[str, Any]:
    """
    Complete emotion workflow analysis for content.
    
    Args:
        content: Content to analyze
        
    Returns:
        Complete workflow results
    """
    try:
        # Split content into segments (simple split by sentences)
        segments = [{"text": s.strip()} for s in content.split(".") if s.strip()]
        
        # Analyze each segment
        analyzed_segments = []
        for segment in segments:
            emotion_result = emotion_analyzer.analyze_emotion(segment["text"])
            segment["emotions"] = emotion_result["emotions"]
            analyzed_segments.append(segment)
        
        # Map trajectory
        trajectory = trajectory_mapper.map_emotion_trajectory(analyzed_segments)
        
        # Detect patterns
        viral_post = ViralPost(
            id="temp",
            author_username="analysis",
            text=content,
            view_count=0,
            share_count=0,
            reply_count=0,
            like_count=0,
            created_at="2024-01-01T00:00:00Z"
        )
        patterns = pattern_extractor.extract_patterns(viral_post)
        
        return {
            "segments": analyzed_segments,
            "trajectory": trajectory,
            "patterns": patterns,
            "recommendations": {
                "should_publish": trajectory.get("metrics", {}).get("consistency", 0) > 0.6,
                "optimal_time": "peak_hours",
                "suggested_improvements": []
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
