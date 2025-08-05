"""RAG Quality Monitoring and Alerting System."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import redis

from services.rag_pipeline.evaluation.rag_evaluator import (
    RAGEvaluator,
    EvaluationMetrics,
)

logger = logging.getLogger(__name__)


@dataclass
class QualityThresholds:
    """Quality thresholds for monitoring."""

    min_relevance_score: float = 0.7
    min_faithfulness_score: float = 0.8
    min_answer_relevance: float = 0.6
    min_overall_score: float = 0.7
    max_response_time_ms: float = 5000
    min_cache_hit_rate: float = 0.6


@dataclass
class QualityAlert:
    """Quality degradation alert."""

    alert_type: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str  # 'warning', 'critical'
    message: str
    timestamp: datetime
    query_examples: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "query_examples": self.query_examples or [],
        }


class RAGQualityMonitor:
    """Monitors RAG pipeline quality in real-time."""

    def __init__(
        self,
        evaluator: RAGEvaluator,
        redis_client: Optional[redis.Redis] = None,
        thresholds: Optional[QualityThresholds] = None,
        registry: Optional[CollectorRegistry] = None,
    ):
        """Initialize quality monitor."""
        self.evaluator = evaluator
        self.redis_client = redis_client
        self.thresholds = thresholds or QualityThresholds()

        # Prometheus metrics
        self.registry = registry or CollectorRegistry()
        self._init_metrics()

        # Alert tracking
        self.active_alerts = {}
        self.alert_callbacks = []

    def _init_metrics(self):
        """Initialize Prometheus metrics."""
        self.quality_metrics = {
            "relevance_score": Gauge(
                "rag_relevance_score", "RAG relevance score", registry=self.registry
            ),
            "faithfulness_score": Gauge(
                "rag_faithfulness_score",
                "RAG faithfulness score",
                registry=self.registry,
            ),
            "answer_relevance": Gauge(
                "rag_answer_relevance",
                "RAG answer relevance score",
                registry=self.registry,
            ),
            "overall_score": Gauge(
                "rag_overall_score", "RAG overall quality score", registry=self.registry
            ),
            "evaluation_latency": Histogram(
                "rag_evaluation_latency_seconds",
                "RAG evaluation latency",
                registry=self.registry,
            ),
            "quality_alerts": Counter(
                "rag_quality_alerts_total",
                "Total quality alerts triggered",
                ["alert_type", "severity"],
                registry=self.registry,
            ),
        }

    async def monitor_query(
        self,
        query: str,
        context: List[str],
        generated_answer: str,
        reference_answer: Optional[str] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Monitor quality of a single query-answer pair."""
        start_time = datetime.utcnow()

        try:
            # Evaluate answer quality
            answer_metrics = await self.evaluator.evaluate_answer_quality(
                query, context, generated_answer, reference_answer
            )

            # Evaluate retrieval quality if documents provided
            retrieval_metrics = None
            if retrieved_docs:
                retrieval_metrics = await self.evaluator.evaluate_retrieval(
                    query, retrieved_docs
                )

            # Calculate overall score
            overall_score = self.evaluator._calculate_overall_score(
                retrieval_metrics, answer_metrics
            )

            # Update metrics
            self._update_prometheus_metrics(answer_metrics, overall_score)

            # Check for quality degradation
            alerts = self._check_quality_thresholds(
                answer_metrics, overall_score, query
            )

            # Store evaluation history
            evaluation_result = {
                "query": query,
                "answer_metrics": answer_metrics.to_dict(),
                "retrieval_metrics": retrieval_metrics.to_dict()
                if retrieval_metrics
                else None,
                "overall_score": overall_score,
                "alerts": [alert.to_dict() for alert in alerts],
                "timestamp": start_time.isoformat(),
                "evaluation_latency_ms": (
                    datetime.utcnow() - start_time
                ).total_seconds()
                * 1000,
            }

            # Store in Redis if available
            if self.redis_client:
                await self._store_evaluation_result(evaluation_result)

            # Trigger alerts
            for alert in alerts:
                await self._trigger_alert(alert)

            return evaluation_result

        except Exception as e:
            logger.error(f"Error monitoring query: {e}")
            return {
                "query": query,
                "error": str(e),
                "timestamp": start_time.isoformat(),
            }

    def _update_prometheus_metrics(
        self, answer_metrics: EvaluationMetrics, overall_score: float
    ):
        """Update Prometheus metrics."""
        if answer_metrics.relevance_score is not None:
            self.quality_metrics["relevance_score"].set(answer_metrics.relevance_score)

        if answer_metrics.faithfulness_score is not None:
            self.quality_metrics["faithfulness_score"].set(
                answer_metrics.faithfulness_score
            )

        if answer_metrics.answer_relevance is not None:
            self.quality_metrics["answer_relevance"].set(
                answer_metrics.answer_relevance
            )

        self.quality_metrics["overall_score"].set(overall_score)

    def _check_quality_thresholds(
        self, answer_metrics: EvaluationMetrics, overall_score: float, query: str
    ) -> List[QualityAlert]:
        """Check if quality metrics meet thresholds."""
        alerts = []

        # Check relevance score
        if (
            answer_metrics.relevance_score is not None
            and answer_metrics.relevance_score < self.thresholds.min_relevance_score
        ):
            alerts.append(
                QualityAlert(
                    alert_type="quality_degradation",
                    metric_name="relevance_score",
                    current_value=answer_metrics.relevance_score,
                    threshold_value=self.thresholds.min_relevance_score,
                    severity="warning",
                    message=f"Relevance score {answer_metrics.relevance_score:.3f} below threshold {self.thresholds.min_relevance_score}",
                    timestamp=datetime.utcnow(),
                    query_examples=[query],
                )
            )

        # Check faithfulness score
        if (
            answer_metrics.faithfulness_score is not None
            and answer_metrics.faithfulness_score
            < self.thresholds.min_faithfulness_score
        ):
            alerts.append(
                QualityAlert(
                    alert_type="hallucination_risk",
                    metric_name="faithfulness_score",
                    current_value=answer_metrics.faithfulness_score,
                    threshold_value=self.thresholds.min_faithfulness_score,
                    severity="critical",
                    message=f"Faithfulness score {answer_metrics.faithfulness_score:.3f} indicates potential hallucination",
                    timestamp=datetime.utcnow(),
                    query_examples=[query],
                )
            )

        # Check answer relevance
        if (
            answer_metrics.answer_relevance is not None
            and answer_metrics.answer_relevance < self.thresholds.min_answer_relevance
        ):
            alerts.append(
                QualityAlert(
                    alert_type="poor_answer_quality",
                    metric_name="answer_relevance",
                    current_value=answer_metrics.answer_relevance,
                    threshold_value=self.thresholds.min_answer_relevance,
                    severity="warning",
                    message=f"Answer relevance {answer_metrics.answer_relevance:.3f} below threshold",
                    timestamp=datetime.utcnow(),
                    query_examples=[query],
                )
            )

        # Check overall score
        if overall_score < self.thresholds.min_overall_score:
            alerts.append(
                QualityAlert(
                    alert_type="overall_quality_degradation",
                    metric_name="overall_score",
                    current_value=overall_score,
                    threshold_value=self.thresholds.min_overall_score,
                    severity="critical" if overall_score < 0.5 else "warning",
                    message=f"Overall quality score {overall_score:.3f} below threshold",
                    timestamp=datetime.utcnow(),
                    query_examples=[query],
                )
            )

        return alerts

    async def _store_evaluation_result(self, result: Dict[str, Any]):
        """Store evaluation result in Redis."""
        try:
            if isinstance(self.redis_client, redis.Redis):
                # Sync Redis client
                key = f"rag_evaluation:{datetime.utcnow().isoformat()}"
                self.redis_client.setex(key, 86400, str(result))  # 24 hour TTL
            else:
                # Async Redis client
                key = f"rag_evaluation:{datetime.utcnow().isoformat()}"
                await self.redis_client.setex(key, 86400, str(result))
        except Exception as e:
            logger.warning(f"Failed to store evaluation result: {e}")

    async def _trigger_alert(self, alert: QualityAlert):
        """Trigger quality alert."""
        # Update Prometheus alert counter
        self.quality_metrics["quality_alerts"].labels(
            alert_type=alert.alert_type, severity=alert.severity
        ).inc()

        # Store active alert
        alert_key = f"{alert.alert_type}:{alert.metric_name}"
        self.active_alerts[alert_key] = alert

        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        logger.warning(f"Quality Alert: {alert.message}")

    def register_alert_callback(self, callback):
        """Register callback for quality alerts."""
        self.alert_callbacks.append(callback)

    async def get_quality_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get quality trends over specified time period."""
        if not self.redis_client:
            return {"error": "Redis not available for trend analysis"}

        try:
            # Get evaluation results from last N hours
            end_time = datetime.utcnow()
            _ = end_time - timedelta(hours=hours)  # start_time for future use

            # This is a simplified implementation
            # In production, you'd want to use Redis Streams or TimeSeries
            results = []

            # Calculate trends
            if results:
                scores = [
                    r.get("overall_score", 0) for r in results if r.get("overall_score")
                ]
                return {
                    "period_hours": hours,
                    "total_evaluations": len(results),
                    "avg_overall_score": statistics.mean(scores) if scores else 0,
                    "min_overall_score": min(scores) if scores else 0,
                    "max_overall_score": max(scores) if scores else 0,
                    "score_trend": "improving"
                    if len(scores) > 1 and scores[-1] > scores[0]
                    else "declining",
                }
            else:
                return {
                    "period_hours": hours,
                    "total_evaluations": 0,
                    "message": "No evaluation data available",
                }

        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return {"error": str(e)}

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active quality alerts."""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    async def batch_monitor(
        self, evaluation_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Monitor quality for multiple cases in batch."""
        tasks = []

        for case in evaluation_cases:
            task = self.monitor_query(
                query=case["query"],
                context=case.get("context", []),
                generated_answer=case.get("generated_answer", ""),
                reference_answer=case.get("reference_answer"),
                retrieved_docs=case.get("retrieved_docs"),
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if not isinstance(result, Exception):
                successful_results.append(result)
            else:
                logger.error(f"Batch monitoring error: {result}")

        return successful_results

    def get_metrics_registry(self) -> CollectorRegistry:
        """Get Prometheus metrics registry."""
        return self.registry
