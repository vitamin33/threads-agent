"""Complete integration test for MLflow tracking in threads-agent."""

from unittest.mock import patch
import os

# Mock the mlflow module before importing our modules
with patch("mlflow.set_tracking_uri"):
    from services.common.mlflow_tracking import MLflowExperimentTracker
    from services.common.mlflow_openai_wrapper import chat_with_tracking
    from services.common.mlflow_config import configure_mlflow


class TestMLflowCompleteIntegration:
    """Integration tests for complete MLflow tracking setup."""

    def test_mlflow_tracks_openai_chat_completion(self):
        """Test that MLflow correctly tracks a simulated OpenAI chat completion."""
        # Arrange
        with (
            patch("mlflow.set_experiment") as mock_set_experiment,
            patch("mlflow.start_run") as mock_start_run,
            patch("mlflow.log_params") as mock_log_params,
            patch("mlflow.log_metrics") as mock_log_metrics,
            patch("mlflow.end_run") as mock_end_run,
            patch("services.common.openai_wrapper.chat") as mock_chat,
        ):
            # Simulate OpenAI response
            mock_chat.return_value = "This is a viral hook about productivity"

            # Act
            response = chat_with_tracking(
                model="gpt-4o",
                prompt="Write a viral hook about productivity",
                persona_id="viral_creator",
            )

            # Assert - verify the response
            assert response == "This is a viral hook about productivity"

            # Assert - verify MLflow tracking
            mock_set_experiment.assert_called_once()
            experiment_name = mock_set_experiment.call_args[0][0]
            assert experiment_name.startswith("viral_creator_")

            mock_start_run.assert_called_once()
            mock_log_params.assert_called_once()
            mock_log_metrics.assert_called_once()
            mock_end_run.assert_called_once()

            # Verify logged parameters
            logged_params = mock_log_params.call_args[0][0]
            assert logged_params["persona_id"] == "viral_creator"
            assert logged_params["model"] == "gpt-4o"
            assert logged_params["prompt"] == "Write a viral hook about productivity"
            assert (
                logged_params["response"] == "This is a viral hook about productivity"
            )

            # Verify logged metrics
            logged_metrics = mock_log_metrics.call_args[0][0]
            assert "prompt_tokens" in logged_metrics
            assert "completion_tokens" in logged_metrics
            assert "total_tokens" in logged_metrics
            assert "latency_ms" in logged_metrics

    def test_mlflow_configuration_from_environment(self):
        """Test that MLflow is configured correctly from environment variables."""
        # Arrange
        with patch.dict(
            os.environ, {"MLFLOW_TRACKING_URI": "http://mlflow.k8s.local:5000"}
        ):
            with patch("mlflow.set_tracking_uri") as mock_set_tracking_uri:
                # Act
                configure_mlflow()

                # Assert
                mock_set_tracking_uri.assert_called_once_with(
                    "http://mlflow.k8s.local:5000"
                )

    def test_end_to_end_tracking_workflow(self):
        """Test complete end-to-end tracking workflow."""
        # Arrange
        with (
            patch("mlflow.set_experiment") as mock_set_experiment,
            patch("mlflow.start_run") as mock_start_run,
            patch("mlflow.log_params") as mock_log_params,
            patch("mlflow.log_metrics") as mock_log_metrics,
            patch("mlflow.end_run") as mock_end_run,
        ):
            # Simulate multiple personas making LLM calls
            personas = [
                ("tech_blogger", "Write about AI trends", "AI is transforming..."),
                ("fitness_coach", "Create workout tips", "Start your day with..."),
                ("chef", "Share a recipe", "Today's special is..."),
            ]

            tracker = MLflowExperimentTracker()

            # Act - track multiple calls
            for persona_id, prompt, response in personas:
                tracker.track_llm_call(
                    persona_id=persona_id,
                    model="gpt-3.5-turbo",
                    prompt=prompt,
                    response=response,
                    prompt_tokens=len(prompt.split()) * 2,
                    completion_tokens=len(response.split()) * 2,
                    latency_ms=100,
                )

            # Assert - verify all calls were tracked
            assert mock_set_experiment.call_count == 3
            assert mock_start_run.call_count == 3
            assert mock_log_params.call_count == 3
            assert mock_log_metrics.call_count == 3
            assert mock_end_run.call_count == 3

            # Verify different experiments for different personas
            experiment_names = [
                call[0][0] for call in mock_set_experiment.call_args_list
            ]
            assert any("tech_blogger_" in name for name in experiment_names)
            assert any("fitness_coach_" in name for name in experiment_names)
            assert any("chef_" in name for name in experiment_names)

    def test_mlflow_tracking_resilience(self):
        """Test that the system continues to work even if MLflow is down."""
        # Arrange
        with (
            patch("mlflow.set_experiment") as mock_set_experiment,
            patch("services.common.openai_wrapper.chat") as mock_chat,
        ):
            # Simulate MLflow being down
            mock_set_experiment.side_effect = Exception("MLflow server unavailable")
            mock_chat.return_value = "Response despite MLflow being down"

            # Act - should not raise exception
            response = chat_with_tracking(
                model="gpt-4o", prompt="Test prompt", persona_id="test_persona"
            )

            # Assert - the main functionality still works
            assert response == "Response despite MLflow being down"
            mock_chat.assert_called_once_with("gpt-4o", "Test prompt")
