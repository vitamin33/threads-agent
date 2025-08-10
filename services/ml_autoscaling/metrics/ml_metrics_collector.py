"""
ML Metrics Collector for Autoscaling Decisions
Collects and analyzes ML-specific metrics from Prometheus
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import numpy as np
from cachetools import TTLCache
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of ML metrics"""
    INFERENCE = "inference"
    TRAINING = "training"
    GPU = "gpu"
    QUEUE = "queue"
    COST = "cost"


@dataclass
class InferenceMetrics:
    """Metrics for inference workloads"""
    service_name: str
    requests_per_second: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0
    tokens_per_second: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingMetrics:
    """Metrics for training jobs"""
    job_name: str
    current_loss: float = 0.0
    loss_trend: str = "stable"  # decreasing, increasing, stable
    epochs_completed: int = 0
    time_per_epoch_seconds: float = 0.0
    estimated_completion_time: Optional[datetime] = None


@dataclass
class GPUMetrics:
    """GPU utilization metrics"""
    avg_utilization: float = 0.0
    max_utilization: float = 0.0
    available_gpus: int = 0
    high_utilization_gpus: int = 0  # GPUs > 90% utilized
    memory_utilization: float = 0.0


@dataclass
class MLWorkloadMetrics:
    """Aggregated ML workload metrics"""
    total_inference_load: float = 0.0
    active_training_jobs: int = 0
    gpu_pressure: str = "low"  # low, medium, high
    queue_depth: int = 0
    recommended_scale_action: Optional[str] = None


@dataclass
class ScalingRecommendation:
    """Scaling recommendation based on metrics"""
    should_scale: bool
    direction: str  # up, down, hold
    target_replicas: int
    reason: str
    confidence: float = 0.0


@dataclass
class CostMetrics:
    """Cost-related metrics"""
    total_cost_usd: float = 0.0
    gpu_cost_usd: float = 0.0
    cpu_cost_usd: float = 0.0
    cost_per_inference: float = 0.0
    spot_savings_potential: float = 0.0


@dataclass
class ModelServingMetrics:
    """Model serving endpoint metrics"""
    model_name: str
    total_requests: int = 0
    error_rate: float = 0.0
    cache_hit_rate: float = 0.0
    model_load_time_ms: float = 0.0


@dataclass
class BatchProcessingMetrics:
    """Batch processing metrics"""
    queue_size: int = 0
    estimated_processing_time_minutes: float = 0.0
    items_per_second: float = 0.0


@dataclass
class PredictiveMetrics:
    """Metrics for predictive scaling"""
    metric_name: str
    predicted_value: float
    confidence_interval: Tuple[float, float]
    pattern_detected: str  # cyclical, trending, stable
    forecast_horizon_minutes: int = 30


@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    detected: bool
    severity: str  # low, medium, high
    description: str
    metric_value: float
    expected_range: Tuple[float, float]


class PrometheusClient:
    """Client for querying Prometheus"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def query(self, query: str) -> Dict[str, Any]:
        """Execute instant query"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/query"
        params = {"query": query}
        
        async with self.session.get(url, params=params) as response:
            return await response.json()

    async def query_range(self, query: str, start: datetime, end: datetime, step: str = "5m") -> Dict[str, Any]:
        """Execute range query"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"{self.base_url}/api/v1/query_range"
        params = {
            "query": query,
            "start": int(start.timestamp()),
            "end": int(end.timestamp()),
            "step": step,
        }
        
        async with self.session.get(url, params=params) as response:
            return await response.json()


class MLMetricsCollector:
    """
    Collector for ML-specific metrics used in autoscaling decisions
    
    This class gathers metrics from various sources and provides
    recommendations for scaling ML infrastructure.
    """

    def __init__(
        self,
        prometheus_url: str = "http://prometheus:9090",
        refresh_interval: int = 30,
        cache_ttl: int = 60,
    ):
        """
        Initialize ML metrics collector
        
        Args:
            prometheus_url: Prometheus server URL
            refresh_interval: How often to refresh metrics (seconds)
            cache_ttl: Cache time-to-live (seconds)
        """
        self.prometheus_url = prometheus_url
        self.refresh_interval = refresh_interval
        self.cache_ttl_seconds = cache_ttl
        self.prometheus = PrometheusClient(prometheus_url)
        self._cache = TTLCache(maxsize=100, ttl=cache_ttl)

    async def collect_inference_metrics(
        self,
        service_name: str,
        lookback_minutes: int = 5,
    ) -> InferenceMetrics:
        """
        Collect inference service metrics
        
        Args:
            service_name: Name of the inference service
            lookback_minutes: How far back to look for metrics
        
        Returns:
            InferenceMetrics object
        """
        metrics = InferenceMetrics(service_name=service_name)
        
        # Query P95 latency
        latency_query = f'histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket{{job="{service_name}"}}[{lookback_minutes}m]))'
        result = await self.prometheus.query(latency_query)
        
        if result['status'] == 'success' and result['data']['result']:
            metrics.p95_latency_ms = float(result['data']['result'][0]['value'][1]) * 1000
        
        # Query request rate
        rps_query = f'rate(vllm_requests_total{{job="{service_name}"}}[{lookback_minutes}m])'
        result = await self.prometheus.query(rps_query)
        
        if result['status'] == 'success' and result['data']['result']:
            metrics.requests_per_second = float(result['data']['result'][0]['value'][1])
        
        return metrics

    async def collect_training_metrics(self, job_name: str) -> TrainingMetrics:
        """
        Collect training job metrics
        
        Args:
            job_name: Name of the training job
        
        Returns:
            TrainingMetrics object
        """
        metrics = TrainingMetrics(job_name=job_name)
        
        # Query training loss over time
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        loss_query = f'training_loss{{job="training", model="{job_name.replace("_training", "")}"}}'
        result = await self.prometheus.query_range(loss_query, start_time, end_time)
        
        if result['status'] == 'success' and result['data']['result']:
            values = result['data']['result'][0]['values']
            if values:
                # Get current loss and trend
                recent_losses = [float(v[1]) for v in values[-3:]]
                metrics.current_loss = recent_losses[-1] if recent_losses else 0.0
                
                # Determine trend
                if len(recent_losses) >= 2:
                    if recent_losses[-1] < recent_losses[-2]:
                        metrics.loss_trend = "decreasing"
                    elif recent_losses[-1] > recent_losses[-2]:
                        metrics.loss_trend = "increasing"
                    else:
                        metrics.loss_trend = "stable"
        
        return metrics

    async def collect_gpu_metrics(self) -> GPUMetrics:
        """
        Collect GPU utilization metrics
        
        Returns:
            GPUMetrics object
        """
        metrics = GPUMetrics()
        
        # Query GPU utilization
        gpu_query = 'gpu_utilization_percent'
        result = await self.prometheus.query(gpu_query)
        
        if result['status'] == 'success' and result['data']['result']:
            utilizations = [float(r['value'][1]) for r in result['data']['result']]
            
            if utilizations:
                metrics.avg_utilization = np.mean(utilizations)
                metrics.max_utilization = max(utilizations)
                metrics.available_gpus = len(utilizations)
                metrics.high_utilization_gpus = sum(1 for u in utilizations if u > 90)
        
        return metrics

    async def get_queue_depth(self, queue_name: str) -> int:
        """
        Get current queue depth
        
        Args:
            queue_name: Name of the queue
        
        Returns:
            Current queue depth
        """
        query = f'rabbitmq_queue_messages{{queue="{queue_name}"}}'
        result = await self.prometheus.query(query)
        
        if result['status'] == 'success' and result['data']['result']:
            return int(float(result['data']['result'][0]['value'][1]))
        
        return 0

    async def calculate_scaling_recommendation(
        self,
        inference_metrics: InferenceMetrics,
        gpu_metrics: GPUMetrics,
        current_replicas: int,
    ) -> ScalingRecommendation:
        """
        Calculate scaling recommendation based on metrics
        
        Args:
            inference_metrics: Current inference metrics
            gpu_metrics: Current GPU metrics
            current_replicas: Current number of replicas
        
        Returns:
            ScalingRecommendation object
        """
        # Default: no scaling
        recommendation = ScalingRecommendation(
            should_scale=False,
            direction="hold",
            target_replicas=current_replicas,
            reason="Metrics within normal range",
            confidence=0.5,
        )
        
        # Check for high latency
        if inference_metrics.p95_latency_ms > 500:
            recommendation.should_scale = True
            recommendation.direction = "up"
            recommendation.target_replicas = min(current_replicas * 2, 10)
            recommendation.reason = f"High P95 latency: {inference_metrics.p95_latency_ms:.0f}ms"
            recommendation.confidence = 0.9
        
        # Check for high GPU utilization
        elif gpu_metrics.avg_utilization > 85:
            recommendation.should_scale = True
            recommendation.direction = "up"
            recommendation.target_replicas = current_replicas + 1
            recommendation.reason = f"High GPU utilization: {gpu_metrics.avg_utilization:.1f}%"
            recommendation.confidence = 0.8
        
        # Check for low utilization (scale down)
        elif inference_metrics.requests_per_second < 1 and current_replicas > 1:
            recommendation.should_scale = True
            recommendation.direction = "down"
            recommendation.target_replicas = max(1, current_replicas - 1)
            recommendation.reason = "Low request rate"
            recommendation.confidence = 0.7
        
        return recommendation

    async def get_batch_processing_metrics(self) -> BatchProcessingMetrics:
        """Get batch processing metrics"""
        metrics = BatchProcessingMetrics()
        
        queue_query = 'batch_processor_queue_size{job="batch-processor"}'
        result = await self.prometheus.query(queue_query)
        
        if result['status'] == 'success' and result['data']['result']:
            metrics.queue_size = int(float(result['data']['result'][0]['value'][1]))
            # Estimate processing time (assuming 10 items/second)
            metrics.items_per_second = 10
            metrics.estimated_processing_time_minutes = metrics.queue_size / (metrics.items_per_second * 60)
        
        return metrics

    async def get_model_serving_metrics(self, model_name: str) -> ModelServingMetrics:
        """Get model serving endpoint metrics"""
        metrics = ModelServingMetrics(model_name=model_name)
        
        # Total requests
        total_query = f'model_inference_requests_total{{model="{model_name}"}}'
        result = await self.prometheus.query(total_query)
        if result['status'] == 'success' and result['data']['result']:
            metrics.total_requests = int(float(result['data']['result'][0]['value'][1]))
        
        # Error rate
        error_query = f'model_inference_errors_total{{model="{model_name}"}}'
        result = await self.prometheus.query(error_query)
        if result['status'] == 'success' and result['data']['result']:
            errors = int(float(result['data']['result'][0]['value'][1]))
            if metrics.total_requests > 0:
                metrics.error_rate = errors / metrics.total_requests
        
        # Cache hit rate
        cache_hits_query = f'model_cache_hits_total{{model="{model_name}"}}'
        result = await self.prometheus.query(cache_hits_query)
        if result['status'] == 'success' and result['data']['result']:
            cache_hits = int(float(result['data']['result'][0]['value'][1]))
            if metrics.total_requests > 0:
                metrics.cache_hit_rate = cache_hits / metrics.total_requests
        
        return metrics

    async def get_cost_metrics(self, lookback_hours: int = 24) -> CostMetrics:
        """Get cost-related metrics"""
        metrics = CostMetrics()
        
        # Mock implementation - would integrate with cloud provider APIs
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        # Query instance costs
        cost_query = 'instance_cost_per_hour_usd'
        result = await self.prometheus.query_range(cost_query, start_time, end_time)
        
        if result['status'] == 'success' and result['data']['result']:
            for series in result['data']['result']:
                instance_type = series['metric'].get('instance_type', '')
                costs = [float(v[1]) for v in series['values']]
                
                if 'gpu' in instance_type.lower():
                    metrics.gpu_cost_usd += sum(costs) * (lookback_hours / len(costs))
                else:
                    metrics.cpu_cost_usd += sum(costs) * (lookback_hours / len(costs))
        
        metrics.total_cost_usd = metrics.gpu_cost_usd + metrics.cpu_cost_usd
        
        # Calculate cost per inference (mock)
        total_inferences = 10000  # Would query from metrics
        if total_inferences > 0:
            metrics.cost_per_inference = metrics.total_cost_usd / total_inferences
        
        return metrics

    async def get_predictive_metrics(
        self,
        metric_name: str,
        lookback_hours: int = 24,
        forecast_hours: int = 1,
    ) -> PredictiveMetrics:
        """Get predictive metrics based on historical data"""
        # Simplified implementation - would use time series forecasting
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)
        
        result = await self.prometheus.query_range(
            metric_name,
            start_time,
            end_time,
            step="5m"
        )
        
        metrics = PredictiveMetrics(
            metric_name=metric_name,
            predicted_value=0.0,
            confidence_interval=(0.0, 0.0),
            pattern_detected="stable",
            forecast_horizon_minutes=forecast_hours * 60,
        )
        
        if result['status'] == 'success' and result['data']['result']:
            values = [float(v[1]) for v in result['data']['result'][0]['values']]
            
            if values:
                # Simple prediction: use recent average
                recent_avg = np.mean(values[-12:])  # Last hour
                std_dev = np.std(values[-12:])
                
                metrics.predicted_value = recent_avg
                metrics.confidence_interval = (
                    recent_avg - 2 * std_dev,
                    recent_avg + 2 * std_dev
                )
                
                # Detect pattern (simplified)
                if std_dev / recent_avg > 0.3:
                    metrics.pattern_detected = "cyclical"
                elif len(values) > 24:
                    trend = np.polyfit(range(len(values)), values, 1)[0]
                    if abs(trend) > 0.1:
                        metrics.pattern_detected = "trending"
        
        return metrics

    async def get_ml_workload_metrics(self) -> MLWorkloadMetrics:
        """Get aggregated ML workload metrics"""
        metrics = MLWorkloadMetrics()
        
        # Aggregate various metrics
        inference_load = await self.prometheus.query('sum(rate(model_inference_requests_total[5m]))')
        if inference_load['status'] == 'success' and inference_load['data']['result']:
            metrics.total_inference_load = float(inference_load['data']['result'][0]['value'][1])
        
        training_jobs = await self.prometheus.query('count(training_job_active == 1)')
        if training_jobs['status'] == 'success' and training_jobs['data']['result']:
            metrics.active_training_jobs = int(float(training_jobs['data']['result'][0]['value'][1]))
        
        gpu_metrics = await self.collect_gpu_metrics()
        if gpu_metrics.avg_utilization > 80:
            metrics.gpu_pressure = "high"
        elif gpu_metrics.avg_utilization > 50:
            metrics.gpu_pressure = "medium"
        else:
            metrics.gpu_pressure = "low"
        
        queue_depth = await self.get_queue_depth("celery")
        metrics.queue_depth = queue_depth
        
        # Determine recommended action
        if metrics.gpu_pressure == "high" or metrics.queue_depth > 100:
            metrics.recommended_scale_action = "scale_up"
        elif metrics.gpu_pressure == "low" and metrics.queue_depth < 10:
            metrics.recommended_scale_action = "scale_down"
        else:
            metrics.recommended_scale_action = "hold"
        
        return metrics

    async def detect_anomaly(
        self,
        metric_name: str,
        threshold_multiplier: float = 2.0,
    ) -> AnomalyDetection:
        """Detect anomalies in metrics"""
        # Query recent metric values
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        result = await self.prometheus.query_range(
            metric_name,
            start_time,
            end_time,
            step="1m"
        )
        
        anomaly = AnomalyDetection(
            detected=False,
            severity="low",
            description="No anomaly detected",
            metric_value=0.0,
            expected_range=(0.0, 0.0),
        )
        
        if result['status'] == 'success' and result['data']['result']:
            values = [float(v[1]) for v in result['data']['result'][0]['values']]
            
            if len(values) > 3:
                # Calculate baseline and detect spikes
                baseline = np.median(values[:-1])
                current = values[-1]
                threshold = baseline * threshold_multiplier
                
                anomaly.metric_value = current
                anomaly.expected_range = (baseline * 0.5, baseline * 1.5)
                
                if current > threshold:
                    anomaly.detected = True
                    anomaly.severity = "high" if current > threshold * 2 else "medium"
                    anomaly.description = f"Spike detected in {metric_name}: {current:.2f} (expected: {baseline:.2f})"
        
        return anomaly

    def get_cached_metric(self, key: str) -> Optional[Any]:
        """Get cached metric value"""
        return self._cache.get(key)

    def set_cached_metric(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached metric value"""
        if ttl is None:
            ttl = self.cache_ttl_seconds
        self._cache[key] = value

    @classmethod
    def for_multi_cluster(cls, cluster_configs: List[Dict[str, str]]) -> 'MultiClusterCollector':
        """Create a multi-cluster collector"""
        return MultiClusterCollector(cluster_configs)


class MultiClusterCollector:
    """Collector for multiple clusters"""
    
    def __init__(self, cluster_configs: List[Dict[str, str]]):
        self.collectors = {
            config['name']: MLMetricsCollector(config['prometheus_url'])
            for config in cluster_configs
        }

    async def collect_all_clusters(self) -> Dict[str, MLWorkloadMetrics]:
        """Collect metrics from all clusters"""
        results = {}
        for name, collector in self.collectors.items():
            results[name] = await collector.get_ml_workload_metrics()
        return results