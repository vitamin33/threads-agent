"""End-to-end integration tests for MLflow tracking with real components."""

import pytest
import os
from unittest.mock import patch
from datetime import datetime

# These tests require MLflow server and are marked with e2e
pytestmark = pytest.mark.e2e

# Skip these imports if running unit tests without MLflow server
try:
    from common.mlflow_config import configure_mlflow  # noqa: F401
    from common.mlflow_tracking import MLflowExperimentTracker  # noqa: F401
    from common.mlflow_openai_wrapper import chat_with_tracking  # noqa: F401
except ImportError:
    # These modules won't be available in unit test mode
    pass


class TestMLflowRealIntegration:
    """Integration tests with actual MLflow components (mocked server)."""

    @pytest.fixture
    def mock_mlflow_server(self):
        """Setup mock MLflow server for testing."""
        with patch("mlflow.set_tracking_uri") as mock_set_uri:
            with patch("mlflow.create_experiment") as mock_create_exp:
                mock_create_exp.return_value = "test-experiment-id"
                yield mock_set_uri, mock_create_exp

    def test_mlflow_configuration_loading(self):
        """Test that MLflow configuration is loaded correctly."""
        # Arrange
        with patch.dict(
            os.environ,
            {
                "MLFLOW_TRACKING_URI": "http://test-mlflow:5000",
                "MLFLOW_EXPERIMENT_NAME": "test-experiment",
            },
        ):
            # Act
            from common.mlflow_config import configure_mlflow

            with patch("mlflow.set_tracking_uri") as mock_set_uri:
                with patch("mlflow.set_experiment"):
                    configure_mlflow()

                    # Assert
                    mock_set_uri.assert_called_with("http://test-mlflow:5000")

    def test_full_workflow_with_real_openai_wrapper(self, mock_mlflow_server):
        """Test the complete workflow with actual OpenAI wrapper integration."""
        # Arrange
        from common.mlflow_openai_wrapper import chat_with_tracking

        # Mock the OpenAI API response (not used directly, but shows expected format)

        with patch("common.openai_wrapper.chat") as mock_chat:
            mock_chat.return_value = "Hello! How can I help you today?"

            with patch("mlflow.set_experiment"):
                with patch("mlflow.start_run") as mock_start_run:
                    with patch("mlflow.log_params") as mock_log_params:
                        with patch("mlflow.log_metrics") as mock_log_metrics:
                            with patch("mlflow.end_run") as mock_end_run:
                                # Act
                                result = chat_with_tracking(
                                    model="gpt-4o",
                                    prompt="Hello",
                                    persona_id="test_persona",
                                )

                                # Assert
                                assert result == "Hello! How can I help you today?"
                                mock_start_run.assert_called_once()
                                mock_log_params.assert_called_once()
                                mock_log_metrics.assert_called_once()
                                mock_end_run.assert_called_once()

    def test_batch_processing_with_mlflow(self):
        """Test batch processing of multiple LLM calls."""
        # Arrange
        from common.mlflow_openai_wrapper import chat_with_tracking

        prompts = [
            ("What is AI?", "persona_1"),
            ("Explain machine learning", "persona_2"),
            ("What is deep learning?", "persona_1"),
        ]

        with patch("common.openai_wrapper.chat") as mock_chat:
            mock_chat.side_effect = [
                "AI is artificial intelligence",
                "ML is a subset of AI",
                "DL uses neural networks",
            ]

            with patch("mlflow.log_metrics") as mock_log_metrics:
                # Act
                results = []
                for prompt, persona in prompts:
                    result = chat_with_tracking(
                        model="gpt-4o", prompt=prompt, persona_id=persona
                    )
                    results.append(result)

                # Assert
                assert len(results) == 3
                assert mock_log_metrics.call_count == 3

    def test_error_recovery_and_logging(self):
        """Test that errors are handled gracefully and logged."""
        # Arrange
        from common.mlflow_openai_wrapper import chat_with_tracking

        with patch("common.openai_wrapper.chat") as mock_chat:
            mock_chat.side_effect = Exception("API Error")

            with patch("common.mlflow_tracking.logger"):
                # Act & Assert
                with pytest.raises(Exception, match="API Error"):
                    chat_with_tracking(
                        model="gpt-4o", prompt="Test", persona_id="test_persona"
                    )

    def test_mlflow_experiment_organization(self):
        """Test that experiments are organized correctly by persona and date."""
        # Arrange
        from common.mlflow_tracking import MLflowExperimentTracker

        tracker = MLflowExperimentTracker()

        with patch("mlflow.set_experiment") as mock_set_exp:
            with patch("mlflow.start_run"):
                with patch("mlflow.log_params"):
                    with patch("mlflow.log_metrics"):
                        with patch("mlflow.end_run"):
                            # Act
                            tracker.track_llm_call(
                                persona_id="viral_content_creator",
                                model="gpt-4o",
                                prompt="Create viral content",
                                response="Here's your viral content",
                                prompt_tokens=5,
                                completion_tokens=10,
                                latency_ms=100,
                            )

                            # Assert
                            experiment_name = mock_set_exp.call_args[0][0]
                            assert "viral_content_creator" in experiment_name
                            assert (
                                datetime.now().strftime("%Y-%m-%d") in experiment_name
                            )

    def test_performance_metrics_tracking(self):
        """Test that performance metrics are tracked accurately."""
        # Arrange
        from common.mlflow_openai_wrapper import chat_with_tracking
        import time

        with patch("common.openai_wrapper.chat") as mock_chat:
            # Simulate varying response times
            def delayed_response(model, prompt):
                if "slow" in prompt:
                    time.sleep(0.2)
                elif "fast" in prompt:
                    time.sleep(0.05)
                else:
                    time.sleep(0.1)
                return f"Response to: {prompt}"

            mock_chat.side_effect = delayed_response

            with patch("mlflow.log_metrics") as mock_log_metrics:
                # Act
                prompts = [
                    ("fast query", 50),  # Expected ~50ms
                    ("slow query", 200),  # Expected ~200ms
                    ("normal query", 100),  # Expected ~100ms
                ]

                for prompt, expected_min_latency in prompts:
                    chat_with_tracking(
                        model="gpt-4o", prompt=prompt, persona_id="test_persona"
                    )

                    # Get the logged latency
                    metrics = mock_log_metrics.call_args[0][0]
                    actual_latency = metrics["latency_ms"]

                    # Assert latency is at least the expected minimum
                    assert actual_latency >= expected_min_latency

    def test_token_usage_aggregation(self):
        """Test aggregation of token usage across multiple calls."""
        # Arrange
        from common.mlflow_openai_wrapper import chat_with_tracking

        total_prompt_tokens = 0
        total_completion_tokens = 0

        with patch("common.openai_wrapper.chat") as mock_chat:
            mock_chat.side_effect = [
                "Short",
                "Medium length response here",
                "This is a much longer response with many more tokens",
            ]

            with patch("mlflow.log_metrics") as mock_log_metrics:
                # Act
                for i, prompt in enumerate(
                    ["Q1", "Question 2", "A longer question here"]
                ):
                    chat_with_tracking(
                        model="gpt-4o", prompt=prompt, persona_id="test_persona"
                    )

                    # Track token usage
                    metrics = mock_log_metrics.call_args_list[i][0][0]
                    total_prompt_tokens += metrics["prompt_tokens"]
                    total_completion_tokens += metrics["completion_tokens"]

                # Assert
                assert total_prompt_tokens > 0
                assert total_completion_tokens > 0
                assert mock_log_metrics.call_count == 3
