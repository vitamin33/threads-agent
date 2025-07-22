# services/viral_engine/quality_gate.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from prometheus_client import Counter, Histogram

from services.viral_engine.engagement_predictor import EngagementPredictor

# Metrics for monitoring
QUALITY_GATE_COUNTER = Counter(
    "quality_gate_evaluations_total",
    "Total quality gate evaluations",
    ["result", "persona_id"],
)
QUALITY_GATE_LATENCY = Histogram(
    "quality_gate_evaluation_seconds", "Quality gate evaluation latency"
)
QUALITY_SCORE_HISTOGRAM = Histogram(
    "quality_gate_scores",
    "Distribution of quality scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


class QualityGate:
    """
    Quality gate system that blocks low-scoring content.
    Uses engagement predictor to ensure only high-quality content is published.
    """

    def __init__(self, min_score: float = 0.7) -> None:
        self.min_score = min_score
        self.engagement_predictor = EngagementPredictor()
        self.rejection_log: list[Dict[str, Any]] = []

    @QUALITY_GATE_LATENCY.time()  # type: ignore[misc]
    def should_publish(
        self, content: str, persona_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate if content should be published based on quality score.

        Args:
            content: The content to evaluate
            persona_id: ID of the persona generating content
            metadata: Additional metadata for tracking

        Returns:
            Tuple of (should_publish, evaluation_details)
        """
        # Get engagement prediction
        prediction = self.engagement_predictor.predict_engagement_rate(content)
        quality_score = prediction["quality_score"]

        # Record score distribution
        QUALITY_SCORE_HISTOGRAM.observe(quality_score)

        # Determine if content passes gate
        passed = quality_score >= self.min_score

        # Create evaluation details
        evaluation = {
            "quality_score": quality_score,
            "threshold": self.min_score,
            "passed": passed,
            "predicted_engagement_rate": prediction["predicted_engagement_rate"],
            "quality_assessment": prediction["quality_assessment"],
            "feature_scores": prediction["feature_scores"],
            "top_factors": prediction["top_factors"],
            "improvement_suggestions": prediction["improvement_suggestions"],
            "persona_id": persona_id,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }

        if passed:
            evaluation["message"] = (
                f"Quality score {quality_score:.2f} meets threshold {self.min_score}"
            )
            QUALITY_GATE_COUNTER.labels(result="passed", persona_id=persona_id).inc()
        else:
            evaluation["message"] = (
                f"Quality score {quality_score:.2f} below threshold {self.min_score}"
            )
            evaluation["rejection_reason"] = self._generate_rejection_reason(prediction)
            self.log_rejection(content, evaluation)
            QUALITY_GATE_COUNTER.labels(result="rejected", persona_id=persona_id).inc()

        return passed, evaluation

    def _generate_rejection_reason(self, prediction: Dict[str, Any]) -> str:
        """Generate human-readable rejection reason"""
        reasons = []

        # Check specific weak areas
        features = prediction["feature_scores"]

        if features.get("hook_strength", 1.0) < 0.3:
            reasons.append("Weak hook - needs stronger opening")

        if features.get("readability", 1.0) < 0.5:
            reasons.append("Poor readability - simplify sentence structure")

        if features.get("emotion_intensity", 1.0) < 0.2:
            reasons.append("Low emotional engagement - add more compelling language")

        if features.get("curiosity_gaps", 1.0) < 0.2:
            reasons.append("Lacks curiosity triggers - add questions or open loops")

        if not reasons:
            reasons.append("Overall quality below threshold - review all suggestions")

        return "; ".join(reasons)

    def log_rejection(self, content: str, evaluation: Dict[str, Any]) -> None:
        """Log rejected content for analysis and improvement"""
        rejection_entry = {
            "content": content[:200] + "..." if len(content) > 200 else content,
            "evaluation": evaluation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.rejection_log.append(rejection_entry)

        # Keep only last 100 rejections in memory
        if len(self.rejection_log) > 100:
            self.rejection_log = self.rejection_log[-100:]

    def get_rejection_analytics(self) -> Dict[str, Any]:
        """Get analytics on rejection patterns"""
        if not self.rejection_log:
            return {"total_rejections": 0, "patterns": {}}

        # Analyze rejection patterns
        rejection_reasons: Dict[str, int] = {}
        personas: Dict[str, int] = {}

        for entry in self.rejection_log:
            # Count rejection reasons
            reason = entry["evaluation"].get("rejection_reason", "Unknown")
            for r in reason.split("; "):
                rejection_reasons[r] = rejection_reasons.get(r, 0) + 1

            # Count by persona
            persona = entry["evaluation"].get("persona_id", "unknown")
            personas[persona] = personas.get(persona, 0) + 1

        return {
            "total_rejections": len(self.rejection_log),
            "rejection_reasons": rejection_reasons,
            "rejections_by_persona": personas,
            "recent_rejections": self.rejection_log[-10:],
        }

    def set_threshold(self, new_threshold: float) -> None:
        """Update quality threshold (for A/B testing)"""
        if 0.0 <= new_threshold <= 1.0:
            self.min_score = new_threshold
        else:
            raise ValueError("Threshold must be between 0 and 1")

    def evaluate_batch(
        self, contents: list[Tuple[str, str]]
    ) -> list[Tuple[bool, Dict[str, Any]]]:
        """Evaluate multiple pieces of content efficiently"""
        results = []
        for content, persona_id in contents:
            results.append(self.should_publish(content, persona_id))
        return results
