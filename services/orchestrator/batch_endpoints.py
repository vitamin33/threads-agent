# services/orchestrator/batch_endpoints.py
"""Batch variant generation endpoints for high-velocity testing"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.common.metrics import (
    record_http_request,
    record_latency,
)
from services.orchestrator.db.models import Base, HookVariant
from services.orchestrator.vector import store_hook_variant

logger = logging.getLogger(__name__)

# Configuration
VIRAL_ENGINE_URL = os.getenv("VIRAL_ENGINE_URL", "http://viral-engine:8080")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/threads_agent")

# Create router
batch_router = APIRouter(prefix="/variants", tags=["variants"])

# Database setup
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)


# Request/Response Models
class TopicInput(BaseModel):
    content: str = Field(..., description="The topic or content to generate variants for")
    category: Optional[str] = Field(None, description="Topic category for pattern selection")


class BatchVariantRequest(BaseModel):
    persona_id: str = Field(..., description="Persona to generate variants for")
    topics: List[TopicInput] = Field(..., description="List of topics to generate variants for")
    variants_per_topic: int = Field(5, ge=3, le=10, description="Number of variants per topic")
    include_emotion_variants: bool = Field(True, description="Include emotion-modified variants")


class VariantResult(BaseModel):
    variant_id: str
    content: str
    pattern: str
    pattern_category: str
    emotion_modifier: Optional[str]
    expected_engagement_rate: float
    template: str


class TopicVariants(BaseModel):
    topic: str
    variants: List[VariantResult]


class BatchVariantResponse(BaseModel):
    batch_id: str
    total_variants: int
    results: List[TopicVariants]
    processing_time_ms: int


class VariantPerformanceUpdate(BaseModel):
    variant_id: str
    actual_engagement_rate: float
    impressions: int
    engagements: int


# Endpoints
@batch_router.post("/generate-batch", response_model=BatchVariantResponse)
async def generate_batch_variants(request: BatchVariantRequest):
    """Generate multiple variants for multiple topics in one efficient call"""
    
    start_time = time.time()
    batch_id = str(uuid.uuid4())
    
    with record_http_request("orchestrator", "POST", "/variants/generate-batch"):
        async with httpx.AsyncClient() as client:
            results = []
            total_variants = 0
            
            # Process topics concurrently
            async def process_topic(topic: TopicInput) -> TopicVariants:
                try:
                    # Call viral engine
                    response = await client.post(
                        f"{VIRAL_ENGINE_URL}/generate-variants",
                        json={
                            "persona_id": request.persona_id,
                            "base_content": topic.content,
                            "topic_category": topic.category,
                            "variant_count": request.variants_per_topic,
                        },
                        timeout=10.0
                    )
                    response.raise_for_status()
                    
                    variants_data = response.json()
                    
                    # Store variants in database
                    with Session(engine) as session:
                        for variant in variants_data:
                            db_variant = HookVariant(
                                variant_id=variant["variant_id"],
                                batch_id=batch_id,
                                pattern_id=variant["pattern"],
                                pattern_category=variant["pattern_category"],
                                emotion_modifier=variant.get("emotion_modifier"),
                                hook_content=variant["content"],
                                expected_engagement_rate=variant["expected_er"],
                                template=variant["template"],
                                original_content=topic.content,
                                persona_id=request.persona_id,
                                created_at=datetime.utcnow()
                            )
                            session.add(db_variant)
                        session.commit()
                    
                    # Store in vector database for similarity search
                    for variant in variants_data:
                        await store_hook_variant(
                            persona_id=request.persona_id,
                            variant_id=variant["variant_id"],
                            content=variant["content"],
                            metadata={
                                "pattern": variant["pattern"],
                                "expected_er": variant["expected_er"],
                                "batch_id": batch_id
                            }
                        )
                    
                    return TopicVariants(
                        topic=topic.content,
                        variants=[VariantResult(**v) for v in variants_data]
                    )
                    
                except Exception as e:
                    logger.error(f"Error processing topic '{topic.content}': {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Failed to process topic: {str(e)}")
            
            # Process all topics concurrently
            topic_results = await asyncio.gather(
                *[process_topic(topic) for topic in request.topics]
            )
            
            for result in topic_results:
                results.append(result)
                total_variants += len(result.variants)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Record metrics
            with record_latency("batch_variant_generation", processing_time_ms / 1000):
                pass
            
            return BatchVariantResponse(
                batch_id=batch_id,
                total_variants=total_variants,
                results=results,
                processing_time_ms=processing_time_ms
            )


@batch_router.get("/batch/{batch_id}")
async def get_batch_variants(batch_id: str):
    """Retrieve all variants from a specific batch"""
    
    with Session(engine) as session:
        variants = session.query(HookVariant).filter_by(batch_id=batch_id).all()
        
        if not variants:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        return {
            "batch_id": batch_id,
            "variants": [
                {
                    "variant_id": v.variant_id,
                    "content": v.hook_content,
                    "pattern": v.pattern_id,
                    "expected_er": v.expected_engagement_rate,
                    "actual_er": v.actual_engagement_rate,
                    "impressions": v.impressions,
                    "selected": v.selected_for_posting
                }
                for v in variants
            ]
        }


@batch_router.post("/performance/update")
async def update_variant_performance(updates: List[VariantPerformanceUpdate]):
    """Update performance metrics for variants after testing"""
    
    with Session(engine) as session:
        for update in updates:
            variant = session.query(HookVariant).filter_by(
                variant_id=update.variant_id
            ).first()
            
            if variant:
                variant.actual_engagement_rate = update.actual_engagement_rate
                variant.impressions = update.impressions
                variant.engagements = update.engagements
                variant.updated_at = datetime.utcnow()
        
        session.commit()
    
    return {"status": "ok", "updated": len(updates)}


@batch_router.get("/performance/top-patterns")
async def get_top_performing_patterns(
    persona_id: Optional[str] = None,
    days: int = 7,
    limit: int = 10
):
    """Get top performing patterns based on actual engagement data"""
    
    with Session(engine) as session:
        # This would be a more complex query in production
        # For now, return mock data structure
        return {
            "patterns": [
                {
                    "pattern_id": "question_009",
                    "pattern_category": "question_hooks",
                    "avg_engagement_rate": 0.095,
                    "usage_count": 42,
                    "template": "What's the difference between {winners} and {losers}? It's not what you think:"
                },
                {
                    "pattern_id": "number_002",
                    "pattern_category": "number_hooks", 
                    "avg_engagement_rate": 0.098,
                    "usage_count": 38,
                    "template": "I analyzed {number} {subjects} and found {finding}:"
                }
            ],
            "recommendation": f"Focus on question and number hooks for {persona_id or 'all personas'}"
        }


@batch_router.post("/experiment/create")
async def create_ab_test_experiment(
    name: str,
    variant_ids: List[str],
    duration_hours: int = 24
):
    """Create an A/B test experiment with selected variants"""
    
    experiment_id = str(uuid.uuid4())
    
    with Session(engine) as session:
        # Mark variants as selected for experiment
        for variant_id in variant_ids:
            variant = session.query(HookVariant).filter_by(
                variant_id=variant_id
            ).first()
            if variant:
                variant.selected_for_posting = True
                variant.experiment_id = experiment_id
        
        session.commit()
    
    return {
        "experiment_id": experiment_id,
        "name": name,
        "variant_count": len(variant_ids),
        "duration_hours": duration_hours,
        "status": "active"
    }