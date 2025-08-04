"""FastAPI service for viral pattern extraction."""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select
import hashlib
from datetime import datetime

from services.viral_scraper.models import ViralPost
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor
from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper
from services.orchestrator.db import get_db_session
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
)


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
    segments: Optional[List[Dict[str, Any]]] = Field(
        None, description="Pre-segmented text pieces"
    )


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
        result = emotion_analyzer.analyze_emotions(request.text)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Emotion analysis failed: {str(e)}"
        )


@app.post("/analyze/emotion-trajectory")
async def analyze_emotion_trajectory(
    request: EmotionTrajectoryRequest, db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Analyze emotion trajectory across content segments.

    Args:
        request: EmotionTrajectoryRequest with segments to analyze
        db: Database session

    Returns:
        Dictionary containing trajectory analysis
    """
    try:
        # Analyze emotions in each segment if not already analyzed
        analyzed_segments = []
        for segment in request.segments:
            if "emotions" not in segment:
                text = segment.get("text", "")
                emotion_result = emotion_analyzer.analyze_emotions(text)
                segment["emotions"] = emotion_result["emotions"]
            analyzed_segments.append(segment)

        # Map trajectory
        trajectory = trajectory_mapper.map_emotion_trajectory(analyzed_segments)

        # Create database record
        content_hash = hashlib.sha256(str(analyzed_segments).encode()).hexdigest()

        db_trajectory = EmotionTrajectory(
            post_id=f"generated_{hash(str(analyzed_segments)) % 100000}",
            persona_id=request.persona_id or "unknown",
            content_hash=content_hash,
            segment_count=len(analyzed_segments),
            total_duration_words=sum(
                len(seg.get("text", "").split()) for seg in analyzed_segments
            ),
            analysis_model="bert_vader_ensemble",
            confidence_score=trajectory.get("metrics", {}).get("consistency", 0.7),
            trajectory_type=trajectory.get("arc_type", "unknown"),
            emotional_variance=trajectory.get("metrics", {}).get("volatility", 0.5),
            peak_count=len(
                [seg for seg in analyzed_segments if seg.get("is_peak", False)]
            ),
            valley_count=len(
                [seg for seg in analyzed_segments if seg.get("is_valley", False)]
            ),
            transition_count=len(trajectory.get("transitions", [])),
            # Average emotion scores
            joy_avg=sum(seg["emotions"].get("joy", 0) for seg in analyzed_segments)
            / len(analyzed_segments),
            anger_avg=sum(seg["emotions"].get("anger", 0) for seg in analyzed_segments)
            / len(analyzed_segments),
            fear_avg=sum(seg["emotions"].get("fear", 0) for seg in analyzed_segments)
            / len(analyzed_segments),
            sadness_avg=sum(
                seg["emotions"].get("sadness", 0) for seg in analyzed_segments
            )
            / len(analyzed_segments),
            surprise_avg=sum(
                seg["emotions"].get("surprise", 0) for seg in analyzed_segments
            )
            / len(analyzed_segments),
            disgust_avg=sum(
                seg["emotions"].get("disgust", 0) for seg in analyzed_segments
            )
            / len(analyzed_segments),
            trust_avg=sum(seg["emotions"].get("trust", 0) for seg in analyzed_segments)
            / len(analyzed_segments),
            anticipation_avg=sum(
                seg["emotions"].get("anticipation", 0) for seg in analyzed_segments
            )
            / len(analyzed_segments),
            sentiment_compound=trajectory.get("metrics", {}).get(
                "overall_sentiment", 0.0
            ),
            processing_time_ms=100,  # Placeholder
        )

        db.add(db_trajectory)
        db.commit()
        db.refresh(db_trajectory)

        # Add database ID to response
        trajectory["trajectory_id"] = db_trajectory.id
        trajectory["persona_id"] = request.persona_id

        return trajectory
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Trajectory analysis failed: {str(e)}"
        )


@app.post("/analyze/emotion-transitions")
async def analyze_emotion_transitions(
    request: EmotionTrajectoryRequest,
) -> Dict[str, Any]:
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
                current["emotions"] = emotion_analyzer.analyze_emotions(
                    current.get("text", "")
                )["emotions"]
            if "emotions" not in next_seg:
                next_seg["emotions"] = emotion_analyzer.analyze_emotions(
                    next_seg.get("text", "")
                )["emotions"]

            # Get dominant emotions
            current_dominant = max(current["emotions"], key=current["emotions"].get)
            next_dominant = max(next_seg["emotions"], key=next_seg["emotions"].get)

            transitions.append(
                {
                    "from_segment": i,
                    "to_segment": i + 1,
                    "from_emotion": current_dominant,
                    "to_emotion": next_dominant,
                    "intensity_change": next_seg["emotions"][next_dominant]
                    - current["emotions"][current_dominant],
                }
            )

        return {
            "transitions": transitions,
            "total_segments": len(request.segments),
            "persona_id": request.persona_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Transition analysis failed: {str(e)}"
        )


@app.post("/templates/emotion", status_code=201)
async def create_emotion_template(
    request: EmotionTemplateRequest, db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Create a new emotion template.

    Args:
        request: EmotionTemplateRequest with template details
        db: Database session

    Returns:
        Created template information
    """
    try:
        # Create database record
        db_template = EmotionTemplate(
            template_name=request.name,
            template_type=request.trajectory_type,
            pattern_description=request.description or "",
            segment_count=len(request.emotion_sequence),
            optimal_duration_words=150,  # Default
            trajectory_pattern=request.trajectory_type,
            primary_emotions=request.emotion_sequence,
            emotion_sequence=str(request.emotion_sequence),  # Store as JSON string
            transition_patterns="{}",  # Empty for now
            usage_count=0,
            average_engagement=0.0,
            effectiveness_score=0.0,
            engagement_correlation=0.0,
            is_active=True,
        )

        db.add(db_template)
        db.commit()
        db.refresh(db_template)

        return {
            "template_id": db_template.id,
            "name": db_template.template_name,
            "trajectory_type": db_template.trajectory_pattern,
            "emotion_sequence": request.emotion_sequence,
            "description": db_template.pattern_description,
            "created_at": db_template.created_at.isoformat()
            if db_template.created_at
            else datetime.now().isoformat(),
            "is_active": db_template.is_active,
            "effectiveness_score": db_template.effectiveness_score,
            "usage_count": db_template.usage_count,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Template creation failed: {str(e)}"
        )


@app.get("/templates/emotion")
async def get_emotion_templates(
    min_effectiveness: Optional[float] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db_session),
) -> List[Dict[str, Any]]:
    """
    Get emotion templates filtered by effectiveness.

    Args:
        min_effectiveness: Minimum effectiveness score
        is_active: Filter by active status
        db: Database session

    Returns:
        List of templates
    """
    try:
        # Build query
        query = select(EmotionTemplate)

        if min_effectiveness is not None:
            query = query.where(
                EmotionTemplate.effectiveness_score >= min_effectiveness
            )
        if is_active is not None:
            query = query.where(EmotionTemplate.is_active == is_active)

        # Execute query
        templates = db.scalars(query).all()

        # Convert to response format
        result = []
        for template in templates:
            result.append(
                {
                    "template_id": template.id,
                    "name": template.template_name,
                    "trajectory_type": template.trajectory_pattern,
                    "effectiveness_score": template.effectiveness_score,
                    "is_active": template.is_active,
                    "usage_count": template.usage_count,
                    "created_at": template.created_at.isoformat()
                    if template.created_at
                    else None,
                }
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve templates: {str(e)}"
        )


@app.get("/trajectories/emotion/{trajectory_id}")
async def get_emotion_trajectory_by_id(
    trajectory_id: int, db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get emotion trajectory by ID.

    Args:
        trajectory_id: Trajectory ID
        db: Database session

    Returns:
        Trajectory details
    """
    try:
        # Query trajectory with segments and transitions
        trajectory = db.get(EmotionTrajectory, trajectory_id)
        if not trajectory:
            raise HTTPException(status_code=404, detail="Trajectory not found")

        # Get segments
        segments = db.scalars(
            select(EmotionSegment)
            .where(EmotionSegment.trajectory_id == trajectory_id)
            .order_by(EmotionSegment.segment_index)
        ).all()

        # Get transitions
        transitions = db.scalars(
            select(EmotionTransition)
            .where(EmotionTransition.trajectory_id == trajectory_id)
            .order_by(EmotionTransition.from_segment_index)
        ).all()

        return {
            "trajectory_id": trajectory.id,
            "post_id": trajectory.post_id,
            "persona_id": trajectory.persona_id,
            "arc_type": trajectory.trajectory_type,
            "confidence_score": trajectory.confidence_score,
            "emotional_variance": trajectory.emotional_variance,
            "segments": [
                {
                    "index": seg.segment_index,
                    "text": seg.content_text,
                    "dominant_emotion": seg.dominant_emotion,
                    "confidence": seg.confidence_score,
                    "is_peak": seg.is_peak,
                    "is_valley": seg.is_valley,
                    "emotions": {
                        "joy": seg.joy_score,
                        "anger": seg.anger_score,
                        "fear": seg.fear_score,
                        "sadness": seg.sadness_score,
                        "surprise": seg.surprise_score,
                        "disgust": seg.disgust_score,
                        "trust": seg.trust_score,
                        "anticipation": seg.anticipation_score,
                    },
                }
                for seg in segments
            ],
            "transitions": [
                {
                    "from_segment": trans.from_segment_index,
                    "to_segment": trans.to_segment_index,
                    "from_emotion": trans.from_emotion,
                    "to_emotion": trans.to_emotion,
                    "intensity_change": trans.intensity_change,
                    "strength_score": trans.strength_score,
                }
                for trans in transitions
            ],
            "metrics": {
                "volatility": trajectory.emotional_variance,
                "consistency": trajectory.confidence_score,
                "peak_intensity": max([seg.confidence_score for seg in segments])
                if segments
                else 0.0,
                "peak_count": trajectory.peak_count,
                "valley_count": trajectory.valley_count,
            },
            "created_at": trajectory.created_at.isoformat()
            if trajectory.created_at
            else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve trajectory: {str(e)}"
        )


@app.get("/trajectories/emotion/persona/{persona_id}")
async def get_emotion_trajectories_by_persona(
    persona_id: str, limit: int = 50, db: Session = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """
    Get all emotion trajectories for a persona.

    Args:
        persona_id: Persona ID
        limit: Maximum number of trajectories to return
        db: Database session

    Returns:
        List of trajectories
    """
    try:
        # Query trajectories for the persona
        trajectories = db.scalars(
            select(EmotionTrajectory)
            .where(EmotionTrajectory.persona_id == persona_id)
            .order_by(EmotionTrajectory.created_at.desc())
            .limit(limit)
        ).all()

        return [
            {
                "trajectory_id": traj.id,
                "post_id": traj.post_id,
                "persona_id": traj.persona_id,
                "arc_type": traj.trajectory_type,
                "confidence_score": traj.confidence_score,
                "segment_count": traj.segment_count,
                "emotional_variance": traj.emotional_variance,
                "peak_count": traj.peak_count,
                "valley_count": traj.valley_count,
                "created_at": traj.created_at.isoformat() if traj.created_at else None,
                "average_emotions": {
                    "joy": traj.joy_avg,
                    "anger": traj.anger_avg,
                    "fear": traj.fear_avg,
                    "sadness": traj.sadness_avg,
                    "surprise": traj.surprise_avg,
                    "disgust": traj.disgust_avg,
                    "trust": traj.trust_avg,
                    "anticipation": traj.anticipation_avg,
                },
            }
            for traj in trajectories
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve trajectories: {str(e)}"
        )


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
            result = emotion_analyzer.analyze_emotions(text)
            elapsed = (time.time() - start) * 1000  # ms

            results.append(
                {
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "emotions": result["emotions"],
                    "dominant_emotion": result["dominant_emotion"],
                    "processing_time_ms": elapsed,
                }
            )
            total_time += elapsed

        return {
            "results": results,
            "total_texts": len(texts),
            "total_processing_time_ms": total_time,
            "average_time_per_text_ms": total_time / len(texts) if texts else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@app.put("/templates/emotion/{template_id}/performance")
async def update_template_performance(
    template_id: int,
    engagement_rate: float,
    views: int,
    db: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Update template performance metrics.

    Args:
        template_id: Template ID
        engagement_rate: Engagement rate
        views: Number of views
        db: Database session

    Returns:
        Updated template
    """
    try:
        # Get existing template
        template = db.get(EmotionTemplate, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Update performance metrics
        old_usage = template.usage_count
        old_avg_engagement = template.average_engagement

        # Calculate new averages
        new_usage_count = old_usage + 1
        new_avg_engagement = (
            (old_avg_engagement * old_usage) + engagement_rate
        ) / new_usage_count

        # Simple effectiveness scoring (can be enhanced with ML models)
        effectiveness_score = min(new_avg_engagement * 8, 1.0)  # Scale to 0-1

        # Update template
        template.usage_count = new_usage_count
        template.average_engagement = new_avg_engagement
        template.effectiveness_score = effectiveness_score
        template.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(template)

        return {
            "template_id": template.id,
            "name": template.template_name,
            "effectiveness_score": template.effectiveness_score,
            "usage_count": template.usage_count,
            "average_engagement": template.average_engagement,
            "updated_at": template.updated_at.isoformat()
            if template.updated_at
            else None,
            "is_active": template.is_active,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update template performance: {str(e)}"
        )


@app.post("/analyze/content-emotion-workflow")
async def analyze_content_emotion_workflow(request: Dict[str, str]) -> Dict[str, Any]:
    """
    Complete emotion workflow analysis for content.

    Args:
        request: Dictionary containing content to analyze

    Returns:
        Complete workflow results
    """
    try:
        content = request.get("content", "")
        # Split content into segments (simple split by sentences)
        segments = [{"text": s.strip()} for s in content.split(".") if s.strip()]

        # Analyze each segment
        analyzed_segments = []
        for segment in segments:
            emotion_result = emotion_analyzer.analyze_emotions(segment["text"])
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
            created_at="2024-01-01T00:00:00Z",
        )
        patterns = pattern_extractor.extract_patterns(viral_post)

        return {
            "segments": analyzed_segments,
            "trajectory": trajectory,
            "patterns": patterns,
            "recommendations": {
                "should_publish": trajectory.get("metrics", {}).get("consistency", 0)
                > 0.6,
                "optimal_time": "peak_hours",
                "suggested_improvements": [],
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Workflow analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
