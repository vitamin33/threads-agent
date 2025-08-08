"""
AI-specific metrics tracking for production monitoring.

Tracks token usage, response times, costs, and confidence scores
to monitor AI system health and detect performance degradation.
"""
from datetime import datetime
from collections import deque
import statistics
from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Summary

# Prometheus metrics for AI monitoring
AI_REQUESTS_TOTAL = Counter(
    'ai_requests_total',
    'Total number of AI inference requests',
    ['model', 'service']
)

AI_ERRORS_TOTAL = Counter(
    'ai_errors_total',
    'Total number of AI inference errors',
    ['model', 'service', 'error_type']
)

AI_RESPONSE_TIME = Histogram(
    'ai_response_time_ms',
    'AI model response time in milliseconds',
    ['model', 'service'],
    buckets=(50, 100, 200, 500, 1000, 2000, 5000, 10000, 30000)
)

AI_TOKENS_TOTAL = Counter(
    'ai_tokens_total',
    'Total tokens consumed by AI models',
    ['model', 'service', 'token_type']
)

AI_COST_DOLLARS = Counter(
    'ai_cost_dollars_total',
    'Total cost in dollars for AI inference',
    ['model', 'service']
)

AI_CONFIDENCE_SCORE = Gauge(
    'ai_confidence_score',
    'Current confidence score of AI model outputs',
    ['model', 'service']
)

AI_CONFIDENCE_DRIFT = Gauge(
    'ai_confidence_drift_percentage',
    'Percentage drift in model confidence',
    ['model', 'service']
)

AI_PROMPT_INJECTIONS = Counter(
    'ai_prompt_injection_attempts_total',
    'Total prompt injection attempts detected',
    ['service', 'severity']
)

AI_HALLUCINATION_FLAGS = Counter(
    'ai_hallucination_flags_total',
    'Total hallucination flags raised',
    ['model', 'service', 'risk_level']
)

AI_SECURITY_INCIDENTS = Counter(
    'ai_security_incidents_total',
    'Total AI security incidents',
    ['service', 'incident_type']
)

AI_ACTIVE_ALERTS = Gauge(
    'ai_active_alerts',
    'Number of currently active AI alerts',
    ['alert_type', 'severity']
)

AI_COST_PER_REQUEST = Summary(
    'ai_cost_per_request',
    'Cost per AI request in dollars',
    ['model', 'service']
)


class AIMetricsTracker:
    """Track AI-specific metrics for monitoring and alerting."""
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics tracker with rolling window.
        
        Args:
            window_size: Number of recent requests to track
        """
        self.window_size = window_size
        self.token_usage = deque(maxlen=window_size)
        self.response_times = deque(maxlen=window_size)
        self.confidence_scores = deque(maxlen=window_size)
        self.model_costs = deque(maxlen=window_size)
        self.error_count = 0
        self.total_requests = 0
        
        # Track by model type
        self.model_metrics: Dict[str, Dict[str, deque]] = {}
        
    def record_inference(
        self,
        model_name: str,
        tokens_used: int,
        response_time_ms: float,
        confidence: Optional[float] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error: bool = False,
        service: str = "unknown"
    ) -> None:
        """
        Record metrics for each AI inference.
        
        Args:
            model_name: Name of the model used (e.g., 'gpt-4', 'gpt-3.5-turbo')
            tokens_used: Total tokens consumed
            response_time_ms: Response time in milliseconds
            confidence: Optional confidence score (0-1)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            error: Whether the inference resulted in an error
            service: Service name making the request
        """
        timestamp = datetime.utcnow()
        self.total_requests += 1
        
        # Emit Prometheus metrics
        AI_REQUESTS_TOTAL.labels(model=model_name, service=service).inc()
        
        if error:
            self.error_count += 1
            AI_ERRORS_TOTAL.labels(model=model_name, service=service, error_type="inference_error").inc()
            return
        
        # Calculate cost based on model
        cost = self._calculate_cost(model_name, prompt_tokens, completion_tokens)
        
        # Emit Prometheus metrics
        AI_RESPONSE_TIME.labels(model=model_name, service=service).observe(response_time_ms)
        AI_TOKENS_TOTAL.labels(model=model_name, service=service, token_type="prompt").inc(prompt_tokens)
        AI_TOKENS_TOTAL.labels(model=model_name, service=service, token_type="completion").inc(completion_tokens)
        AI_COST_DOLLARS.labels(model=model_name, service=service).inc(cost)
        AI_COST_PER_REQUEST.labels(model=model_name, service=service).observe(cost)
        
        if confidence is not None:
            AI_CONFIDENCE_SCORE.labels(model=model_name, service=service).set(confidence)
        
        # Update global metrics
        self.token_usage.append(tokens_used)
        self.response_times.append(response_time_ms)
        self.model_costs.append(cost)
        
        if confidence is not None:
            self.confidence_scores.append(confidence)
        
        # Update per-model metrics
        if model_name not in self.model_metrics:
            self.model_metrics[model_name] = {
                'response_times': deque(maxlen=self.window_size),
                'token_usage': deque(maxlen=self.window_size),
                'costs': deque(maxlen=self.window_size)
            }
        
        self.model_metrics[model_name]['response_times'].append(response_time_ms)
        self.model_metrics[model_name]['token_usage'].append(tokens_used)
        self.model_metrics[model_name]['costs'].append(cost)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current AI metrics for monitoring."""
        metrics = {
            'total_requests': self.total_requests,
            'error_rate': self.error_count / max(1, self.total_requests),
            'avg_tokens_per_request': self._safe_mean(self.token_usage),
            'avg_response_time_ms': self._safe_mean(self.response_times),
            'p95_response_time_ms': self._safe_percentile(self.response_times, 95),
            'p99_response_time_ms': self._safe_percentile(self.response_times, 99),
            'total_cost_last_window': sum(self.model_costs),
            'cost_per_request': self._safe_mean(self.model_costs),
            'avg_confidence': self._safe_mean(self.confidence_scores),
            'confidence_trend': self._detect_confidence_drift(),
            'model_breakdown': self._get_model_breakdown()
        }
        
        return metrics
    
    def _calculate_cost(self, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost based on OpenAI pricing.
        
        Pricing as of 2024:
        - GPT-4: $0.03/1K prompt tokens, $0.06/1K completion tokens
        - GPT-3.5-turbo: $0.0005/1K prompt tokens, $0.0015/1K completion tokens
        """
        pricing = {
            'gpt-4': {'prompt': 0.03, 'completion': 0.06},
            'gpt-4o': {'prompt': 0.005, 'completion': 0.015},
            'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
            'gpt-3.5-turbo-0125': {'prompt': 0.0005, 'completion': 0.0015}
        }
        
        if model_name in pricing:
            cost = (
                prompt_tokens * pricing[model_name]['prompt'] + 
                completion_tokens * pricing[model_name]['completion']
            ) / 1000
            return cost
        
        # Default pricing for unknown models
        return (prompt_tokens * 0.001 + completion_tokens * 0.002) / 1000
    
    def _detect_confidence_drift(self) -> str:
        """
        Simple drift detection based on confidence scores.
        
        Compares recent confidence scores against baseline to detect
        potential model performance degradation.
        """
        if len(self.confidence_scores) < 100:
            return "insufficient_data"
        
        # Compare last 100 vs previous 100
        recent = list(self.confidence_scores)[-100:]
        previous = list(self.confidence_scores)[-200:-100]
        
        if not previous:
            return "no_baseline"
        
        recent_avg = statistics.mean(recent)
        previous_avg = statistics.mean(previous)
        
        # Calculate drift percentage
        if previous_avg > 0:
            drift_percentage = ((previous_avg - recent_avg) / previous_avg) * 100
        else:
            drift_percentage = 0
        
        # Emit drift metrics to Prometheus for all models
        for model_name in self.model_metrics.keys():
            AI_CONFIDENCE_DRIFT.labels(model=model_name, service="global").set(abs(drift_percentage))
        
        # Categorize drift
        if abs(drift_percentage) > 15:
            return f"significant_drift_{drift_percentage:+.1f}%"
        elif abs(drift_percentage) > 10:
            return f"moderate_drift_{drift_percentage:+.1f}%"
        elif abs(drift_percentage) > 5:
            return f"minor_drift_{drift_percentage:+.1f}%"
        
        return "stable"
    
    def _get_model_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Get metrics breakdown by model type."""
        breakdown = {}
        
        for model_name, metrics in self.model_metrics.items():
            breakdown[model_name] = {
                'request_count': len(metrics['response_times']),
                'avg_response_time_ms': self._safe_mean(metrics['response_times']),
                'avg_tokens': self._safe_mean(metrics['token_usage']),
                'total_cost': sum(metrics['costs'])
            }
        
        return breakdown
    
    def _safe_mean(self, data: deque) -> float:
        """Calculate mean with empty check."""
        return statistics.mean(data) if data else 0.0
    
    def _safe_percentile(self, data: deque, percentile: int) -> float:
        """Calculate percentile with safety checks."""
        if not data:
            return 0.0
        
        if len(data) < 20:
            return max(data)
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global instance for easy access
ai_metrics = AIMetricsTracker()