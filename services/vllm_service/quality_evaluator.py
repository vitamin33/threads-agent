"""
Quality Evaluator - Measure and compare vLLM output quality vs OpenAI
"""

import time
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality evaluation metrics"""

    request_id: str
    vllm_response: str
    openai_response: Optional[str]
    length_score: float
    coherence_score: float
    engagement_score: float
    overall_quality: float
    timestamp: float


class QualityEvaluator:
    """Evaluate and compare response quality"""

    def __init__(self):
        self.evaluations: List[QualityMetrics] = []
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.8,
            "acceptable": 0.7,
            "poor": 0.5,
        }

    async def evaluate_response(
        self, prompt: str, vllm_response: str, openai_response: Optional[str] = None
    ) -> QualityMetrics:
        """Evaluate response quality using multiple metrics"""
        request_id = hashlib.md5(f"{prompt}:{time.time()}".encode()).hexdigest()[:8]

        # Calculate individual quality scores
        length_score = self._evaluate_length(vllm_response, prompt)
        coherence_score = self._evaluate_coherence(vllm_response)
        engagement_score = self._evaluate_engagement(vllm_response)

        # Calculate overall quality score (weighted average)
        overall_quality = (
            length_score * 0.2 + coherence_score * 0.4 + engagement_score * 0.4
        )

        metrics = QualityMetrics(
            request_id=request_id,
            vllm_response=vllm_response,
            openai_response=openai_response,
            length_score=length_score,
            coherence_score=coherence_score,
            engagement_score=engagement_score,
            overall_quality=overall_quality,
            timestamp=time.time(),
        )

        self.evaluations.append(metrics)

        logger.info(
            f"Quality evaluation {request_id}: "
            f"Overall={overall_quality:.3f}, "
            f"Coherence={coherence_score:.3f}, "
            f"Engagement={engagement_score:.3f}"
        )

        return metrics

    def _evaluate_length(self, response: str, prompt: str) -> float:
        """Evaluate response length appropriateness"""
        response_len = len(response.split())
        prompt_len = len(prompt.split())

        # Ideal response length is 2-5x the prompt length
        ratio = response_len / max(prompt_len, 1)

        if 2 <= ratio <= 5:
            return 1.0
        elif 1.5 <= ratio < 2 or 5 < ratio <= 7:
            return 0.8
        elif 1 <= ratio < 1.5 or 7 < ratio <= 10:
            return 0.6
        else:
            return 0.4

    def _evaluate_coherence(self, response: str) -> float:
        """Evaluate response coherence and structure"""
        score = 0.0

        # Check for proper sentence structure
        sentences = re.split(r"[.!?]+", response)
        valid_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if len(valid_sentences) >= 2:
            score += 0.3

        # Check for proper capitalization
        if response[0].isupper():
            score += 0.1

        # Check for logical flow (simple heuristic)
        transition_words = [
            "however",
            "therefore",
            "moreover",
            "furthermore",
            "additionally",
            "consequently",
            "meanwhile",
            "similarly",
            "in contrast",
            "for example",
        ]

        transition_count = sum(
            1 for word in transition_words if word.lower() in response.lower()
        )
        if transition_count > 0:
            score += min(0.2, transition_count * 0.05)

        # Check for balanced paragraph structure
        paragraphs = response.split("\n\n")
        if 1 < len(paragraphs) <= 5:
            score += 0.2

        # Check for proper punctuation
        punct_score = min(0.2, response.count(".") * 0.02 + response.count("!") * 0.01)
        score += punct_score

        return min(1.0, score)

    def _evaluate_engagement(self, response: str) -> float:
        """Evaluate response engagement and viral potential"""
        score = 0.0
        response_lower = response.lower()

        # Check for engaging elements
        engaging_patterns = [
            (r"\?", 0.1, "questions"),  # Questions engage readers
            (r"!", 0.05, "exclamations"),  # Exclamation marks show enthusiasm
            (r"\b(you|your)\b", 0.15, "personal_address"),  # Direct address
            (r"\b(why|how|what|when|where)\b", 0.1, "interrogatives"),
            (r"\b(secret|truth|reveal|discover)\b", 0.1, "curiosity_words"),
            (
                r"\b(amazing|incredible|shocking|surprising)\b",
                0.08,
                "strong_adjectives",
            ),
            (r"\b\d+[%]?\b", 0.05, "numbers_stats"),  # Numbers and stats
            (r":", 0.02, "colons"),  # Lists and explanations
        ]

        for pattern, weight, category in engaging_patterns:
            matches = len(re.findall(pattern, response, re.IGNORECASE))
            contribution = min(weight, matches * weight * 0.5)
            score += contribution

        # Check for storytelling elements
        story_elements = ["first", "then", "finally", "suddenly", "imagine", "picture"]
        story_count = sum(1 for element in story_elements if element in response_lower)
        score += min(0.15, story_count * 0.03)

        # Check for contrarian/opinion language
        opinion_words = [
            "unpopular opinion",
            "controversial",
            "truth is",
            "reality check",
            "here's why",
            "the problem with",
            "most people",
        ]
        opinion_count = sum(1 for phrase in opinion_words if phrase in response_lower)
        score += min(0.2, opinion_count * 0.1)

        # Penalize too much promotional language
        promo_words = ["buy", "purchase", "sale", "discount", "offer", "deal"]
        promo_count = sum(1 for word in promo_words if word in response_lower)
        if promo_count > 2:
            score -= 0.1

        return min(1.0, max(0.0, score))

    async def get_metrics(self) -> Dict:
        """Get comprehensive quality metrics"""
        if not self.evaluations:
            return {
                "total_evaluations": 0,
                "average_quality": 0.0,
                "quality_distribution": {},
                "trending_quality": 0.0,
            }

        # Calculate overall statistics
        total_evals = len(self.evaluations)
        avg_quality = sum(e.overall_quality for e in self.evaluations) / total_evals
        avg_coherence = sum(e.coherence_score for e in self.evaluations) / total_evals
        avg_engagement = sum(e.engagement_score for e in self.evaluations) / total_evals

        # Quality distribution
        distribution = {"excellent": 0, "good": 0, "acceptable": 0, "poor": 0}
        for eval in self.evaluations:
            if eval.overall_quality >= self.quality_thresholds["excellent"]:
                distribution["excellent"] += 1
            elif eval.overall_quality >= self.quality_thresholds["good"]:
                distribution["good"] += 1
            elif eval.overall_quality >= self.quality_thresholds["acceptable"]:
                distribution["acceptable"] += 1
            else:
                distribution["poor"] += 1

        # Trending quality (last 10 evaluations vs overall)
        recent_evals = (
            self.evaluations[-10:] if len(self.evaluations) >= 10 else self.evaluations
        )
        recent_avg = sum(e.overall_quality for e in recent_evals) / len(recent_evals)

        return {
            "total_evaluations": total_evals,
            "average_quality": avg_quality,
            "average_coherence": avg_coherence,
            "average_engagement": avg_engagement,
            "quality_distribution": distribution,
            "quality_percentages": {
                k: (v / total_evals * 100) for k, v in distribution.items()
            },
            "trending_quality": recent_avg,
            "quality_trend": "improving"
            if recent_avg > avg_quality
            else "stable"
            if abs(recent_avg - avg_quality) < 0.05
            else "declining",
            "benchmarks": {
                "target_quality": 0.8,
                "current_vs_target": (avg_quality / 0.8 * 100) if avg_quality else 0,
                "passing_rate": (distribution["excellent"] + distribution["good"])
                / total_evals
                * 100,
            },
        }

    def get_quality_category(self, score: float) -> str:
        """Get quality category for a score"""
        for category, threshold in sorted(
            self.quality_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if score >= threshold:
                return category
        return "poor"


# Global instance
quality_evaluator = QualityEvaluator()
