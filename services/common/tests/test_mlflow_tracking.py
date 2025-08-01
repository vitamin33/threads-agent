"""Test suite for MLflow experiment tracking following TDD principles."""

import pytest
from unittest.mock import Mock, patch

# Patch configure_mlflow before importing to prevent side effects
with patch("common.mlflow_config.configure_mlflow"):
    from common.mlflow_tracking import MLflowExperimentTracker, track_llm_call


class TestMLflowExperimentTracker:
    """Test cases for MLflow experiment tracking of LLM calls."""

    def test_tracker_logs_llm_call_to_mlflow(self):
        """Test that LLM calls are logged to MLflow with all required fields."""
        # Arrange
        with (
            patch("mlflow.set_experiment"),
            patch("mlflow.start_run") as mock_start_run,
            patch("mlflow.log_params") as mock_log_params,
            patch("mlflow.log_metrics") as mock_log_metrics,
            patch("mlflow.end_run") as mock_end_run,
        ):
            tracker = MLflowExperimentTracker()

            # Act
            tracker.track_llm_call(
                persona_id="test_persona",
                model="gpt-4o",
                prompt="Write a test",
                response="This is a test response",
                prompt_tokens=10,
                completion_tokens=20,
                latency_ms=150,
            )

            # Assert
            mock_start_run.assert_called_once()
            mock_log_params.assert_called_once()
            mock_log_metrics.assert_called_once()
            mock_end_run.assert_called_once()

    def test_tracker_logs_correct_parameters(self):
        """Test that the tracker logs the correct parameters to MLflow."""
        # Arrange
        with (
            patch("mlflow.set_experiment"),
            patch("mlflow.start_run"),
            patch("mlflow.log_params") as mock_log_params,
            patch("mlflow.log_metrics"),
            patch("mlflow.end_run"),
        ):
            tracker = MLflowExperimentTracker()

            # Act
            tracker.track_llm_call(
                persona_id="test_persona",
                model="gpt-4o",
                prompt="Write a test",
                response="This is a test response",
                prompt_tokens=10,
                completion_tokens=20,
                latency_ms=150,
            )

            # Assert
            expected_params = {
                "persona_id": "test_persona",
                "model": "gpt-4o",
                "prompt": "Write a test",
                "response": "This is a test response",
            }
            mock_log_params.assert_called_once_with(expected_params)

    def test_tracker_logs_correct_metrics(self):
        """Test that the tracker logs the correct metrics to MLflow."""
        # Arrange
        with (
            patch("mlflow.set_experiment"),
            patch("mlflow.start_run"),
            patch("mlflow.log_params"),
            patch("mlflow.log_metrics") as mock_log_metrics,
            patch("mlflow.end_run"),
        ):
            tracker = MLflowExperimentTracker()

            # Act
            tracker.track_llm_call(
                persona_id="test_persona",
                model="gpt-4o",
                prompt="Write a test",
                response="This is a test response",
                prompt_tokens=10,
                completion_tokens=20,
                latency_ms=150,
            )

            # Assert
            expected_metrics = {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
                "latency_ms": 150,
            }
            mock_log_metrics.assert_called_once_with(expected_metrics)

    def test_tracker_sets_experiment_by_persona_and_date(self):
        """Test that the tracker organizes experiments by persona and date."""
        # Arrange
        with (
            patch("mlflow.set_experiment") as mock_set_experiment,
            patch("mlflow.start_run"),
            patch("mlflow.log_params"),
            patch("mlflow.log_metrics"),
            patch("mlflow.end_run"),
        ):
            with patch("common.mlflow_tracking.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "2024-01-15"

                tracker = MLflowExperimentTracker()

                # Act
                tracker.track_llm_call(
                    persona_id="test_persona",
                    model="gpt-4o",
                    prompt="Write a test",
                    response="This is a test response",
                    prompt_tokens=10,
                    completion_tokens=20,
                    latency_ms=150,
                )

                # Assert
                expected_experiment_name = "test_persona_2024-01-15"
                mock_set_experiment.assert_called_once_with(expected_experiment_name)

    def test_tracker_handles_mlflow_server_unavailable_gracefully(self):
        """Test that the tracker handles MLflow server unavailability gracefully."""
        # Arrange
        with patch("mlflow.set_experiment") as mock_set_experiment:
            # Simulate MLflow server being unavailable
            mock_set_experiment.side_effect = Exception("Connection refused")

            tracker = MLflowExperimentTracker()

            # Act - should not raise an exception
            tracker.track_llm_call(
                persona_id="test_persona",
                model="gpt-4o",
                prompt="Write a test",
                response="This is a test response",
                prompt_tokens=10,
                completion_tokens=20,
                latency_ms=150,
            )

            # Assert - we got here without raising an exception
            assert True


class TestMLflowTrackingDecorator:
    """Test cases for the MLflow tracking decorator."""

    @pytest.mark.asyncio
    async def test_decorator_tracks_async_llm_calls(self):
        """Test that the decorator tracks async LLM calls automatically."""
        # Arrange
        with patch(
            "common.mlflow_tracking.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            # Create a mock response object similar to OpenAI's response
            mock_response = Mock()
            mock_response.model = "gpt-4o"
            mock_response.usage = Mock(
                prompt_tokens=10, completion_tokens=20, total_tokens=30
            )
            mock_response.choices = [Mock(message=Mock(content="Test response"))]

            # Define an async function decorated with track_llm_call
            @track_llm_call(persona_id="test_persona")
            async def call_llm(prompt: str):
                # Simulate OpenAI API call
                return mock_response

            # Act
            result = await call_llm("Test prompt")

            # Assert
            assert result == mock_response
            mock_tracker.track_llm_call.assert_called_once()
