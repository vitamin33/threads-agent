# services/viral_engine/main.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.common.metrics import maybe_start_metrics_server

from .hook_optimizer import ViralHookEngine

maybe_start_metrics_server()

api = FastAPI(title="viral-engine", description="Viral content optimization service")
app = api

# Initialize the viral hook engine
hook_engine = ViralHookEngine()


class HookOptimizationRequest(BaseModel):
    persona_id: str = Field(
        ..., examples=["ai-jesus"], description="Persona identifier"
    )
    base_content: str = Field(
        ...,
        examples=["AI will change everything"],
        description="Base content to optimize",
    )
    topic_category: Optional[str] = Field(
        None, examples=["technology"], description="Content topic category"
    )
    target_audience: Optional[str] = Field(
        None, examples=["entrepreneurs"], description="Target audience"
    )
    posting_time: Optional[str] = Field(
        None, examples=["morning"], description="When content will be posted"
    )


class HookOptimizationResponse(BaseModel):
    original_hook: str
    optimized_hooks: List[Dict[str, Any]]
    selected_pattern: str
    expected_engagement_rate: float
    optimization_reason: str


class PatternPerformanceRequest(BaseModel):
    persona_id: str = Field(..., examples=["ai-jesus"])
    time_period_days: int = Field(
        7, description="Days to look back for performance data"
    )


@api.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "viral-engine"}


@api.get("/patterns")
async def list_patterns() -> Dict[str, Any]:
    """Get all available hook patterns"""
    patterns = hook_engine.get_available_patterns()
    return {
        "total_patterns": len(patterns),
        "categories": hook_engine.get_pattern_categories(),
        "patterns": patterns,
    }


@api.post("/optimize-hook", response_model=HookOptimizationResponse)
async def optimize_hook(req: HookOptimizationRequest) -> HookOptimizationResponse:
    """Optimize a hook using viral patterns"""
    try:
        result = await hook_engine.optimize_hook(
            persona_id=req.persona_id,
            base_content=req.base_content,
            topic_category=req.topic_category,
            target_audience=req.target_audience,
            posting_time=req.posting_time,
        )
        return HookOptimizationResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Hook optimization failed: {str(e)}"
        )


@api.post("/generate-variants")
async def generate_hook_variants(req: HookOptimizationRequest) -> Dict[str, Any]:
    """Generate multiple hook variants for A/B testing"""
    try:
        variants = await hook_engine.generate_variants(
            persona_id=req.persona_id,
            base_content=req.base_content,
            topic_category=req.topic_category,
            variant_count=5,
        )
        return {"variants": variants, "generation_time": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Variant generation failed: {str(e)}"
        )


@api.post("/pattern-performance")
async def get_pattern_performance(req: PatternPerformanceRequest) -> Dict[str, Any]:
    """Get performance analytics for patterns"""
    try:
        performance = await hook_engine.get_pattern_performance(
            persona_id=req.persona_id, time_period_days=req.time_period_days
        )
        return performance
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Performance analysis failed: {str(e)}"
        )


@api.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint"""
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
