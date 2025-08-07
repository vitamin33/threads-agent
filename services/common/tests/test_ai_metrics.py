"""Tests for AI metrics tracking system."""
import pytest
from services.common.ai_metrics import AIMetricsTracker


class TestAIMetricsTracker:
    """Test AI-specific metrics tracking."""
    
    def test_record_inference_success(self):
        """Test recording successful inference metrics."""
        tracker = AIMetricsTracker(window_size=10)
        
        # Record a successful inference
        tracker.record_inference(
            model_name="gpt-3.5-turbo",
            tokens_used=150,
            response_time_ms=250.5,
            confidence=0.85,
            prompt_tokens=100,
            completion_tokens=50,
            error=False
        )
        
        metrics = tracker.get_metrics()
        
        assert metrics['total_requests'] == 1
        assert metrics['error_rate'] == 0.0
        assert metrics['avg_tokens_per_request'] == 150
        assert metrics['avg_response_time_ms'] == 250.5
        assert metrics['avg_confidence'] == 0.85
        assert metrics['cost_per_request'] > 0  # Should calculate cost
        
    def test_record_inference_error(self):
        """Test recording failed inference."""
        tracker = AIMetricsTracker()
        
        # Record an error
        tracker.record_inference(
            model_name="gpt-4",
            tokens_used=0,
            response_time_ms=100,
            error=True
        )
        
        metrics = tracker.get_metrics()
        
        assert metrics['total_requests'] == 1
        assert metrics['error_rate'] == 1.0
        assert metrics['avg_tokens_per_request'] == 0  # No tokens for errors
        
    def test_cost_calculation(self):
        """Test OpenAI cost calculation."""
        tracker = AIMetricsTracker()
        
        # Test GPT-4 pricing
        cost_gpt4 = tracker._calculate_cost("gpt-4", prompt_tokens=1000, completion_tokens=1000)
        expected_gpt4 = (1000 * 0.03 + 1000 * 0.06) / 1000  # $0.09
        assert abs(cost_gpt4 - expected_gpt4) < 0.001
        
        # Test GPT-3.5-turbo pricing
        cost_gpt35 = tracker._calculate_cost("gpt-3.5-turbo", prompt_tokens=1000, completion_tokens=1000)
        expected_gpt35 = (1000 * 0.0005 + 1000 * 0.0015) / 1000  # $0.002
        assert abs(cost_gpt35 - expected_gpt35) < 0.0001
        
    def test_confidence_drift_detection(self):
        """Test model confidence drift detection."""
        tracker = AIMetricsTracker(window_size=300)
        
        # Add baseline confidence scores
        for _ in range(100):
            tracker.record_inference(
                model_name="gpt-4",
                tokens_used=100,
                response_time_ms=200,
                confidence=0.90
            )
        
        # Add drifted confidence scores
        for _ in range(100):
            tracker.record_inference(
                model_name="gpt-4",
                tokens_used=100,
                response_time_ms=200,
                confidence=0.75  # 16.7% drop
            )
        
        metrics = tracker.get_metrics()
        
        # Should detect significant drift
        assert "significant_drift" in metrics['confidence_trend']
        assert "-16.7%" in metrics['confidence_trend']
        
    def test_percentile_calculations(self):
        """Test p95 and p99 response time calculations."""
        tracker = AIMetricsTracker()
        
        # Add varied response times
        response_times = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000] * 5
        for rt in response_times:
            tracker.record_inference(
                model_name="gpt-3.5-turbo",
                tokens_used=100,
                response_time_ms=rt
            )
        
        metrics = tracker.get_metrics()
        
        # P95 should be around 950ms
        assert 900 <= metrics['p95_response_time_ms'] <= 1000
        # P99 should be close to 1000ms
        assert 950 <= metrics['p99_response_time_ms'] <= 1000
        
    def test_model_breakdown(self):
        """Test metrics breakdown by model."""
        tracker = AIMetricsTracker()
        
        # Record for different models
        tracker.record_inference("gpt-4", 200, 300)
        tracker.record_inference("gpt-4", 250, 350)
        tracker.record_inference("gpt-3.5-turbo", 100, 150)
        
        metrics = tracker.get_metrics()
        breakdown = metrics['model_breakdown']
        
        assert "gpt-4" in breakdown
        assert "gpt-3.5-turbo" in breakdown
        assert breakdown['gpt-4']['request_count'] == 2
        assert breakdown['gpt-4']['avg_tokens'] == 225  # (200+250)/2
        assert breakdown['gpt-3.5-turbo']['request_count'] == 1