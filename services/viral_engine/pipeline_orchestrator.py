# services/viral_engine/pipeline_orchestrator.py
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Tuple

from prometheus_client import Counter, Histogram

from services.viral_engine.engagement_predictor import EngagementPredictor
from services.viral_engine.hook_optimizer import HookOptimizer
from services.viral_engine.quality_gate import QualityGate
from services.viral_engine.reply_magnetizer import ReplyMagnetizer

# Metrics for monitoring
PIPELINE_COUNTER = Counter(
    "viral_pipeline_executions_total",
    "Total pipeline executions",
    ["stage", "result"],
)
PIPELINE_LATENCY = Histogram(
    "viral_pipeline_latency_seconds",
    "Pipeline execution latency",
    ["stage"],
)
PIPELINE_SUCCESS_RATE = Histogram(
    "viral_pipeline_success_rate",
    "Success rate through pipeline stages",
)


class PipelineOrchestrator:
    """
    Orchestrates the viral engine pipeline components.
    Coordinates: Hook Optimizer → Quality Gate → Reply Magnetizer
    """

    def __init__(
        self,
        quality_threshold: float = 0.7,
        enable_hook_optimization: bool = True,
        enable_reply_magnets: bool = True,
    ) -> None:
        # Initialize components
        self.hook_optimizer = HookOptimizer() if enable_hook_optimization else None
        self.quality_gate = QualityGate(min_score=quality_threshold)
        self.reply_magnetizer = ReplyMagnetizer() if enable_reply_magnets else None
        self.engagement_predictor = EngagementPredictor()

        # Configuration
        self.enable_hook_optimization = enable_hook_optimization
        self.enable_reply_magnets = enable_reply_magnets

        # Pipeline stats
        self.pipeline_stats = {
            "total_processed": 0,
            "passed_quality_gate": 0,
            "hook_optimized": 0,
            "magnets_added": 0,
        }

    async def process_content(
        self,
        content: str,
        persona_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process content through the viral engine pipeline.

        Args:
            content: Raw content to process
            persona_id: ID of the persona
            metadata: Additional metadata

        Returns:
            Pipeline result with enhanced content and metrics
        """
        result: Dict[str, Any] = {
            "original_content": content,
            "persona_id": persona_id,
            "metadata": metadata or {},
            "pipeline_stages": {},
            "success": False,
        }

        try:
            # Stage 1: Hook Optimization (optional)
            if self.enable_hook_optimization and self.hook_optimizer:
                with PIPELINE_LATENCY.labels(stage="hook_optimization").time():
                    optimized = await self.hook_optimizer.optimize_hook(
                        persona_id, content
                    )

                    result["pipeline_stages"]["hook_optimization"] = {
                        "success": True,
                        "optimized_content": optimized["optimized_hook"],
                        "pattern_used": optimized["pattern"]["name"],
                        "predicted_ctr_boost": optimized["predicted_ctr_boost"],
                    }

                    # Update content for next stage
                    content = optimized["optimized_hook"]
                    self.pipeline_stats["hook_optimized"] += 1

                    PIPELINE_COUNTER.labels(
                        stage="hook_optimization", result="success"
                    ).inc()

            # Stage 2: Quality Gate (required)
            with PIPELINE_LATENCY.labels(stage="quality_gate").time():
                passed, evaluation = self.quality_gate.should_publish(
                    content, persona_id, metadata
                )

                result["pipeline_stages"]["quality_gate"] = {
                    "passed": passed,
                    "quality_score": evaluation["quality_score"],
                    "threshold": evaluation["threshold"],
                    "evaluation": evaluation,
                }

                if not passed:
                    # Content rejected - stop pipeline
                    result["success"] = False
                    result["rejection_reason"] = evaluation.get("rejection_reason")
                    result["improvement_suggestions"] = evaluation.get(
                        "improvement_suggestions", []
                    )

                    PIPELINE_COUNTER.labels(
                        stage="quality_gate", result="rejected"
                    ).inc()
                    return result

                self.pipeline_stats["passed_quality_gate"] += 1
                PIPELINE_COUNTER.labels(stage="quality_gate", result="passed").inc()

            # Stage 3: Reply Magnetizer (optional)
            if self.enable_reply_magnets and self.reply_magnetizer:
                with PIPELINE_LATENCY.labels(stage="reply_magnetizer").time():
                    enhanced_content, magnet_metadata = (
                        self.reply_magnetizer.inject_reply_magnets(
                            content, persona_id, magnet_count=1
                        )
                    )

                    result["pipeline_stages"]["reply_magnetizer"] = {
                        "success": True,
                        "enhanced_content": enhanced_content,
                        "magnets_injected": magnet_metadata,
                        "magnet_count": len(magnet_metadata),
                    }

                    # Update content for final output
                    content = enhanced_content
                    self.pipeline_stats["magnets_added"] += len(magnet_metadata)

                    PIPELINE_COUNTER.labels(
                        stage="reply_magnetizer", result="success"
                    ).inc()

            # Final result
            result["final_content"] = content
            result["success"] = True
            self.pipeline_stats["total_processed"] += 1

            # Calculate success rate
            if self.pipeline_stats["total_processed"] > 0:
                success_rate = (
                    self.pipeline_stats["passed_quality_gate"]
                    / self.pipeline_stats["total_processed"]
                )
                PIPELINE_SUCCESS_RATE.observe(success_rate)

            return result

        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            PIPELINE_COUNTER.labels(stage="pipeline", result="error").inc()
            return result

    async def process_batch(
        self, content_items: list[Tuple[str, str, Optional[Dict[str, Any]]]]
    ) -> list[Dict[str, Any]]:
        """
        Process multiple content items through the pipeline.

        Args:
            content_items: List of (content, persona_id, metadata) tuples

        Returns:
            List of pipeline results
        """
        tasks = [
            self.process_content(content, persona_id, metadata)
            for content, persona_id, metadata in content_items
        ]

        return await asyncio.gather(*tasks)

    def get_pipeline_analytics(self) -> Dict[str, Any]:
        """Get analytics on pipeline performance"""
        analytics = {
            "pipeline_stats": self.pipeline_stats.copy(),
            "quality_gate_analytics": self.quality_gate.get_rejection_analytics(),
        }

        if self.reply_magnetizer:
            analytics["magnet_performance"] = (
                self.reply_magnetizer.get_magnet_performance()
            )

        # Calculate rates
        if self.pipeline_stats["total_processed"] > 0:
            total = self.pipeline_stats["total_processed"]
            analytics["rates"] = {
                "quality_pass_rate": self.pipeline_stats["passed_quality_gate"] / total,
                "hook_optimization_rate": self.pipeline_stats["hook_optimized"] / total,
                "magnet_injection_rate": (
                    self.pipeline_stats["magnets_added"] / total
                    if self.enable_reply_magnets
                    else 0
                ),
            }
        else:
            analytics["rates"] = {
                "quality_pass_rate": 0,
                "hook_optimization_rate": 0,
                "magnet_injection_rate": 0,
            }

        return analytics

    def update_configuration(
        self,
        quality_threshold: Optional[float] = None,
        enable_hook_optimization: Optional[bool] = None,
        enable_reply_magnets: Optional[bool] = None,
    ) -> None:
        """Update pipeline configuration (for A/B testing)"""
        if quality_threshold is not None:
            self.quality_gate.set_threshold(quality_threshold)

        if enable_hook_optimization is not None:
            self.enable_hook_optimization = enable_hook_optimization
            if enable_hook_optimization and not self.hook_optimizer:
                self.hook_optimizer = HookOptimizer()

        if enable_reply_magnets is not None:
            self.enable_reply_magnets = enable_reply_magnets
            if enable_reply_magnets and not self.reply_magnetizer:
                self.reply_magnetizer = ReplyMagnetizer()

    def reset_stats(self) -> None:
        """Reset pipeline statistics"""
        self.pipeline_stats = {
            "total_processed": 0,
            "passed_quality_gate": 0,
            "hook_optimized": 0,
            "magnets_added": 0,
        }
