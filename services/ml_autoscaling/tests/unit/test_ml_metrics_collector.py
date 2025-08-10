"""
Test suite for ML Metrics Collector
TDD approach - testing ML-specific metrics collection for autoscaling
"""

import pytest
from unittest.mock import Mock, patch

# These imports will fail initially (TDD)
from services.ml_autoscaling.metrics.ml_metrics_collector import (
    MLMetricsCollector,
    MLWorkloadMetrics,
    InferenceMetrics,
    TrainingMetrics,
    GPUMetrics,
)


class TestMLMetricsCollector:
    """Test cases for ML-specific metrics collection"""

    @pytest.fixture
    def collector(self):
        """Create ML metrics collector instance"""
        return MLMetricsCollector(
            prometheus_url="http://prometheus:9090",
            refresh_interval=30,
        )

    @pytest.fixture
    def mock_prometheus_client(self):
        """Mock Prometheus client"""
        with patch(
            "services.ml_autoscaling.metrics.ml_metrics_collector.PrometheusClient"
        ) as mock:
            client = Mock()
            mock.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_collect_inference_metrics(self, collector, mock_prometheus_client):
        """Test collecting inference-specific metrics"""
        # Arrange
        mock_prometheus_client.query.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"job": "vllm-service"},
                        "value": [1234567890, "0.250"],  # 250ms latency
                    }
                ]
            },
        }

        # Act
        metrics = await collector.collect_inference_metrics(
            service_name="vllm-service",
            lookback_minutes=5,
        )

        # Assert
        assert isinstance(metrics, InferenceMetrics)
        assert metrics.p95_latency_ms == 250
        assert metrics.service_name == "vllm-service"
        mock_prometheus_client.query.assert_called()

    @pytest.mark.asyncio
    async def test_collect_training_metrics(self, collector, mock_prometheus_client):
        """Test collecting training job metrics"""
        # Arrange
        mock_prometheus_client.query_range.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"job": "training", "model": "engagement_predictor"},
                        "values": [
                            [1234567890, "0.92"],  # Loss value
                            [1234567900, "0.85"],
                            [1234567910, "0.78"],
                        ],
                    }
                ]
            },
        }

        # Act
        metrics = await collector.collect_training_metrics(
            job_name="engagement_predictor_training",
        )

        # Assert
        assert isinstance(metrics, TrainingMetrics)
        assert metrics.current_loss == 0.78
        assert metrics.loss_trend == "decreasing"
        assert metrics.job_name == "engagement_predictor_training"

    @pytest.mark.asyncio
    async def test_collect_gpu_metrics(self, collector, mock_prometheus_client):
        """Test collecting GPU utilization metrics"""
        # Arrange
        mock_prometheus_client.query.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"gpu": "0", "node": "gpu-node-1"},
                        "value": [1234567890, "85.5"],
                    },
                    {
                        "metric": {"gpu": "1", "node": "gpu-node-1"},
                        "value": [1234567890, "92.3"],
                    },
                ]
            },
        }

        # Act
        metrics = await collector.collect_gpu_metrics()

        # Assert
        assert isinstance(metrics, GPUMetrics)
        assert metrics.avg_utilization == 88.9  # Average of 85.5 and 92.3
        assert metrics.max_utilization == 92.3
        assert metrics.available_gpus == 2
        assert metrics.high_utilization_gpus == 1  # One GPU > 90%

    @pytest.mark.asyncio
    async def test_calculate_queue_depth(self, collector, mock_prometheus_client):
        """Test calculating queue depth for Celery workers"""
        # Arrange
        mock_prometheus_client.query.return_value = {
            "status": "success",
            "data": {
                "result": [{"metric": {"queue": "celery"}, "value": [1234567890, "42"]}]
            },
        }

        # Act
        queue_depth = await collector.get_queue_depth("celery")

        # Assert
        assert queue_depth == 42
        mock_prometheus_client.query.assert_called_with(
            'rabbitmq_queue_messages{queue="celery"}'
        )

    @pytest.mark.asyncio
    async def test_calculate_scaling_recommendation(self, collector):
        """Test calculating scaling recommendations based on metrics"""
        # Arrange
        inference_metrics = InferenceMetrics(
            service_name="vllm-service",
            requests_per_second=50,
            p95_latency_ms=800,  # High latency
            p99_latency_ms=1200,
            error_rate=0.02,
            tokens_per_second=5000,
        )

        gpu_metrics = GPUMetrics(
            avg_utilization=85,
            max_utilization=95,
            available_gpus=4,
            high_utilization_gpus=3,
        )

        # Act
        recommendation = await collector.calculate_scaling_recommendation(
            inference_metrics=inference_metrics,
            gpu_metrics=gpu_metrics,
            current_replicas=2,
        )

        # Assert
        assert recommendation.should_scale == True
        assert recommendation.direction == "up"
        assert recommendation.target_replicas == 4  # Double due to high latency
        assert "High P95 latency" in recommendation.reason

    @pytest.mark.asyncio
    async def test_batch_processing_metrics(self, collector, mock_prometheus_client):
        """Test metrics for batch processing workloads"""
        # Arrange
        mock_prometheus_client.query.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"job": "batch-processor"},
                        "value": [1234567890, "1500"],  # Items in batch queue
                    }
                ]
            },
        }

        # Act
        batch_metrics = await collector.get_batch_processing_metrics()

        # Assert
        assert batch_metrics.queue_size == 1500
        assert batch_metrics.estimated_processing_time_minutes > 0

    @pytest.mark.asyncio
    async def test_model_serving_metrics(self, collector, mock_prometheus_client):
        """Test model serving endpoint metrics"""
        # Arrange
        mock_responses = {
            "model_inference_requests_total": 10000,
            "model_inference_errors_total": 50,
            "model_cache_hits_total": 8000,
            "model_cache_misses_total": 2000,
        }

        mock_prometheus_client.query.side_effect = lambda q: {
            "status": "success",
            "data": {
                "result": [
                    {"value": [1234567890, str(mock_responses.get(q.split("{")[0], 0))]}
                ]
            },
        }

        # Act
        serving_metrics = await collector.get_model_serving_metrics("engagement_model")

        # Assert
        assert serving_metrics.total_requests == 10000
        assert serving_metrics.error_rate == 0.005  # 50/10000
        assert serving_metrics.cache_hit_rate == 0.8  # 8000/10000

    @pytest.mark.asyncio
    async def test_cost_metrics_collection(self, collector, mock_prometheus_client):
        """Test collecting cost-related metrics for optimization"""
        # Arrange
        mock_prometheus_client.query_range.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"instance_type": "g4dn.xlarge"},
                        "values": [
                            [1234567890, "0.526"],  # Cost per hour
                        ],
                    }
                ]
            },
        }

        # Act
        cost_metrics = await collector.get_cost_metrics(
            lookback_hours=24,
        )

        # Assert
        assert cost_metrics.total_cost_usd > 0
        assert cost_metrics.gpu_cost_usd > 0
        assert cost_metrics.cost_per_inference < 0.01  # Should be cents per inference

    @pytest.mark.asyncio
    async def test_predictive_metrics(self, collector, mock_prometheus_client):
        """Test collecting metrics for predictive scaling"""
        # Arrange
        # Mock historical data with pattern
        historical_values = [
            [1234567890 + i * 300, str(10 + i % 20)]  # Cyclical pattern
            for i in range(288)  # 24 hours of 5-minute samples
        ]

        mock_prometheus_client.query_range.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {"metric": {"job": "orchestrator"}, "values": historical_values}
                ]
            },
        }

        # Act
        predictive_metrics = await collector.get_predictive_metrics(
            metric_name="request_rate",
            lookback_hours=24,
            forecast_hours=1,
        )

        # Assert
        assert predictive_metrics.predicted_value > 0
        assert predictive_metrics.confidence_interval is not None
        assert predictive_metrics.pattern_detected in ["cyclical", "trending", "stable"]

    @pytest.mark.asyncio
    async def test_aggregated_ml_workload_metrics(
        self, collector, mock_prometheus_client
    ):
        """Test aggregating all ML workload metrics"""
        # Arrange
        mock_prometheus_client.query.side_effect = [
            # Inference metrics
            {"status": "success", "data": {"result": [{"value": [1234567890, "100"]}]}},
            # Training metrics
            {"status": "success", "data": {"result": [{"value": [1234567890, "2"]}]}},
            # GPU metrics
            {"status": "success", "data": {"result": [{"value": [1234567890, "75"]}]}},
            # Queue depth
            {"status": "success", "data": {"result": [{"value": [1234567890, "50"]}]}},
        ]

        # Act
        workload_metrics = await collector.get_ml_workload_metrics()

        # Assert
        assert isinstance(workload_metrics, MLWorkloadMetrics)
        assert workload_metrics.total_inference_load > 0
        assert workload_metrics.active_training_jobs >= 0
        assert workload_metrics.gpu_pressure in ["low", "medium", "high"]
        assert workload_metrics.recommended_scale_action is not None

    def test_metrics_caching(self, collector):
        """Test metrics caching to avoid excessive Prometheus queries"""
        # Arrange
        collector.cache_ttl_seconds = 60

        # Act
        cached_value = collector.get_cached_metric("test_metric")
        collector.set_cached_metric("test_metric", 42, ttl=60)
        retrieved_value = collector.get_cached_metric("test_metric")

        # Assert
        assert cached_value is None
        assert retrieved_value == 42

    @pytest.mark.asyncio
    async def test_alert_on_anomaly(self, collector, mock_prometheus_client):
        """Test anomaly detection in metrics"""
        # Arrange
        # Mock sudden spike in latency
        mock_prometheus_client.query_range.return_value = {
            "status": "success",
            "data": {
                "result": [
                    {
                        "metric": {"job": "vllm-service"},
                        "values": [
                            [1234567890, "100"],  # Normal
                            [1234567900, "105"],
                            [1234567910, "500"],  # Spike!
                        ],
                    }
                ]
            },
        }

        # Act
        anomaly = await collector.detect_anomaly(
            metric_name="inference_latency",
            threshold_multiplier=2.0,
        )

        # Assert
        assert anomaly.detected == True
        assert anomaly.severity in ["low", "medium", "high"]
        assert "spike" in anomaly.description.lower()

    @pytest.mark.asyncio
    async def test_multi_cluster_metrics(self, collector):
        """Test collecting metrics from multiple clusters"""
        # Arrange
        cluster_configs = [
            {"name": "prod", "prometheus_url": "http://prod-prometheus:9090"},
            {"name": "staging", "prometheus_url": "http://staging-prometheus:9090"},
        ]

        # Act
        multi_cluster_collector = MLMetricsCollector.for_multi_cluster(cluster_configs)
        all_metrics = await multi_cluster_collector.collect_all_clusters()

        # Assert
        assert len(all_metrics) == 2
        assert "prod" in all_metrics
        assert "staging" in all_metrics
