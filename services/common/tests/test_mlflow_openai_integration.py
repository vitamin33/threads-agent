"""Test suite for MLflow integration with OpenAI wrapper."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from services.common.mlflow_tracking import MLflowExperimentTracker


class TestMLflowOpenAIIntegration:
    """Test cases for MLflow integration with OpenAI wrapper."""

    def test_mlflow_tracker_can_be_integrated_with_openai_wrapper(self):
        """Test that MLflow tracker can be added to existing OpenAI wrapper."""
        # Arrange
        with patch(
            "services.common.mlflow_tracking.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            # Import and use the openai wrapper
            from services.common import openai_wrapper

            # Assert - the wrapper module exists and can be imported
            assert openai_wrapper is not None
            assert hasattr(openai_wrapper, "track_cost")

            # We can create an MLflow tracker instance
            tracker = MLflowExperimentTracker()
            assert tracker is not None

    def test_enhanced_chat_function_tracks_to_mlflow(self):
        """Test that the enhanced chat function tracks calls to MLflow."""
        # Arrange
        mock_tracker = Mock()

        # Patch MLflowExperimentTracker at the import location in mlflow_openai_wrapper
        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            # Import the enhanced wrapper
            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = "Test response"

                # Act
                result = chat_with_tracking(
                    model="gpt-4o", prompt="Test prompt", persona_id="test_persona"
                )

                # Assert
                assert result == "Test response"
                mock_chat.assert_called_once_with("gpt-4o", "Test prompt")
                mock_tracker.track_llm_call.assert_called_once()

                # Verify the call arguments
                call_args = mock_tracker.track_llm_call.call_args
                assert call_args.kwargs["persona_id"] == "test_persona"
                assert call_args.kwargs["model"] == "gpt-4o"
                assert call_args.kwargs["prompt"] == "Test prompt"
                assert call_args.kwargs["response"] == "Test response"
                assert "prompt_tokens" in call_args.kwargs
                assert "completion_tokens" in call_args.kwargs
                assert "latency_ms" in call_args.kwargs

    def test_chat_with_tracking_empty_prompt(self):
        """Test handling of empty prompts."""
        # Arrange
        mock_tracker = Mock()

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = ""

                # Act
                result = chat_with_tracking(
                    model="gpt-4o", prompt="", persona_id="test_persona"
                )

                # Assert
                assert result == ""
                mock_chat.assert_called_once_with("gpt-4o", "")
                mock_tracker.track_llm_call.assert_called_once()

                # Verify empty prompt is tracked correctly
                call_args = mock_tracker.track_llm_call.call_args
                assert call_args.kwargs["prompt"] == ""
                assert call_args.kwargs["prompt_tokens"] == 0
                assert call_args.kwargs["completion_tokens"] == 0

    def test_chat_with_tracking_long_response(self):
        """Test handling of long responses with proper token estimation."""
        # Arrange
        mock_tracker = Mock()
        long_response = " ".join(["word"] * 1000)  # 1000 words

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = long_response

                # Act
                result = chat_with_tracking(
                    model="gpt-4o",
                    prompt="Generate a long response",
                    persona_id="test_persona",
                )

                # Assert
                assert result == long_response
                call_args = mock_tracker.track_llm_call.call_args
                # Rough estimation: 1000 words * 2 = 2000 tokens
                assert call_args.kwargs["completion_tokens"] == 2000
                assert call_args.kwargs["prompt_tokens"] == 8  # 4 words * 2

    @pytest.mark.parametrize(
        "model,prompt,persona_id",
        [
            ("gpt-3.5-turbo", "Test prompt", "persona_1"),
            ("gpt-4", "Another prompt", "persona_2"),
            ("gpt-4o-mini", "Mini model test", "persona_3"),
        ],
    )
    def test_chat_with_tracking_different_models(self, model, prompt, persona_id):
        """Test tracking works with different model configurations."""
        # Arrange
        mock_tracker = Mock()

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = f"Response for {model}"

                # Act
                result = chat_with_tracking(
                    model=model, prompt=prompt, persona_id=persona_id
                )

                # Assert
                assert result == f"Response for {model}"
                mock_chat.assert_called_once_with(model, prompt)

                call_args = mock_tracker.track_llm_call.call_args
                assert call_args.kwargs["model"] == model
                assert call_args.kwargs["prompt"] == prompt
                assert call_args.kwargs["persona_id"] == persona_id

    def test_chat_with_tracking_latency_measurement(self):
        """Test that latency is measured correctly."""
        # Arrange
        mock_tracker = Mock()

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                # Simulate a 100ms delay
                def delayed_response(*args):
                    time.sleep(0.1)
                    return "Delayed response"

                mock_chat.side_effect = delayed_response

                # Act
                start = time.time()
                result = chat_with_tracking(
                    model="gpt-4o", prompt="Test", persona_id="test_persona"
                )
                duration = time.time() - start

                # Assert
                assert result == "Delayed response"
                call_args = mock_tracker.track_llm_call.call_args
                latency_ms = call_args.kwargs["latency_ms"]

                # Latency should be at least 100ms
                assert latency_ms >= 100
                # But not more than total duration + small buffer
                assert latency_ms <= (duration * 1000) + 50

    def test_chat_with_tracking_special_characters(self):
        """Test handling of special characters in prompts and responses."""
        # Arrange
        mock_tracker = Mock()
        special_prompt = "Test with émojis 🚀 and special chars: <>\n\t"
        special_response = "Response with special chars: €£¥ and line\nbreaks"

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = special_response

                # Act
                result = chat_with_tracking(
                    model="gpt-4o", prompt=special_prompt, persona_id="test_persona"
                )

                # Assert
                assert result == special_response
                call_args = mock_tracker.track_llm_call.call_args
                assert call_args.kwargs["prompt"] == special_prompt
                assert call_args.kwargs["response"] == special_response


class TestMLflowExperimentTracker:
    """Test cases for the MLflowExperimentTracker class."""

    @patch("services.common.mlflow_tracking.mlflow")
    def test_track_llm_call_success(self, mock_mlflow):
        """Test successful tracking of LLM call."""
        # Arrange
        tracker = MLflowExperimentTracker()

        # Act
        tracker.track_llm_call(
            persona_id="test_persona",
            model="gpt-4o",
            prompt="Test prompt",
            response="Test response",
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=150,
        )

        # Assert
        mock_mlflow.set_experiment.assert_called_once()
        experiment_name = mock_mlflow.set_experiment.call_args[0][0]
        assert experiment_name.startswith("test_persona_")

        mock_mlflow.start_run.assert_called_once()
        mock_mlflow.log_params.assert_called_once_with(
            {
                "persona_id": "test_persona",
                "model": "gpt-4o",
                "prompt": "Test prompt",
                "response": "Test response",
            }
        )
        mock_mlflow.log_metrics.assert_called_once_with(
            {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
                "latency_ms": 150,
            }
        )
        mock_mlflow.end_run.assert_called_once()

    @patch("services.common.mlflow_tracking.mlflow")
    @patch("services.common.mlflow_tracking.logger")
    def test_track_llm_call_mlflow_failure(self, mock_logger, mock_mlflow):
        """Test graceful handling when MLflow tracking fails."""
        # Arrange
        tracker = MLflowExperimentTracker()
        mock_mlflow.set_experiment.side_effect = Exception("MLflow connection error")

        # Act
        tracker.track_llm_call(
            persona_id="test_persona",
            model="gpt-4o",
            prompt="Test prompt",
            response="Test response",
            prompt_tokens=10,
            completion_tokens=20,
            latency_ms=150,
        )

        # Assert - should log warning but not raise exception
        mock_logger.warning.assert_called_once()
        assert (
            "Failed to track LLM call to MLflow" in mock_logger.warning.call_args[0][0]
        )

    @patch("services.common.mlflow_tracking.mlflow")
    def test_track_llm_call_with_zero_tokens(self, mock_mlflow):
        """Test tracking with zero tokens."""
        # Arrange
        tracker = MLflowExperimentTracker()

        # Act
        tracker.track_llm_call(
            persona_id="test_persona",
            model="gpt-4o",
            prompt="",
            response="",
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=10,
        )

        # Assert
        mock_mlflow.log_metrics.assert_called_once_with(
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "latency_ms": 10,
            }
        )

    @patch("services.common.mlflow_tracking.mlflow")
    @patch("services.common.mlflow_tracking.datetime")
    def test_experiment_naming_with_date(self, mock_datetime, mock_mlflow):
        """Test that experiment names include correct date formatting."""
        # Arrange
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-15"
        mock_datetime.now.return_value = mock_now

        tracker = MLflowExperimentTracker()

        # Act
        tracker.track_llm_call(
            persona_id="test_persona",
            model="gpt-4o",
            prompt="Test",
            response="Response",
            prompt_tokens=5,
            completion_tokens=10,
            latency_ms=50,
        )

        # Assert
        mock_mlflow.set_experiment.assert_called_once_with("test_persona_2024-01-15")


class TestMLflowDecorator:
    """Test cases for the async decorator functionality."""

    @pytest.mark.asyncio
    async def test_track_llm_call_decorator_basic(self):
        """Test the decorator tracks async function calls."""
        # Arrange
        from services.common.mlflow_tracking import track_llm_call

        # Create a mock response object
        mock_response = MagicMock()
        mock_response.model = "gpt-4o"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Test response"

        @track_llm_call(persona_id="test_persona")
        async def mock_llm_call(prompt: str):
            return mock_response

        with patch(
            "services.common.mlflow_tracking.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            # Act
            result = await mock_llm_call("Test prompt")

            # Assert
            assert result == mock_response
            mock_tracker.track_llm_call.assert_called_once()

            call_args = mock_tracker.track_llm_call.call_args
            assert call_args.kwargs["persona_id"] == "test_persona"
            assert call_args.kwargs["model"] == "gpt-4o"
            assert call_args.kwargs["prompt"] == "Test prompt"
            assert call_args.kwargs["response"] == "Test response"
            assert call_args.kwargs["prompt_tokens"] == 10
            assert call_args.kwargs["completion_tokens"] == 20

    @pytest.mark.asyncio
    async def test_track_llm_call_decorator_with_messages(self):
        """Test the decorator handles chat completion format with messages."""
        # Arrange
        from services.common.mlflow_tracking import track_llm_call

        mock_response = MagicMock()
        mock_response.model = "gpt-4"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 25
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Chat response"

        @track_llm_call(persona_id="chat_persona")
        async def mock_chat_completion(messages):
            return mock_response

        with patch(
            "services.common.mlflow_tracking.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            # Act
            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ]
            result = await mock_chat_completion(messages=messages)

            # Assert
            assert result == mock_response
            mock_tracker.track_llm_call.assert_called_once()

            call_args = mock_tracker.track_llm_call.call_args
            assert call_args.kwargs["prompt"] == str(messages)
            assert call_args.kwargs["response"] == "Chat response"

    @pytest.mark.asyncio
    async def test_track_llm_call_decorator_error_handling(self):
        """Test the decorator handles errors in the wrapped function."""
        # Arrange
        from services.common.mlflow_tracking import track_llm_call

        @track_llm_call(persona_id="error_persona")
        async def failing_llm_call(prompt: str):
            raise ValueError("LLM call failed")

        with patch(
            "services.common.mlflow_tracking.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            # Act & Assert
            with pytest.raises(ValueError, match="LLM call failed"):
                await failing_llm_call("Test prompt")

            # Tracking should not be called on error
            mock_tracker.track_llm_call.assert_not_called()


class TestMLflowIntegration:
    """Integration tests that verify the full flow."""

    @pytest.mark.e2e
    def test_end_to_end_tracking_flow(self):
        """Test the complete flow from chat call to MLflow tracking."""
        # This test would require actual MLflow server running
        # Marked as e2e for integration testing

        # Arrange
        with patch("services.common.mlflow_tracking.mlflow") as mock_mlflow:
            # Mock successful MLflow operations
            mock_mlflow.set_experiment.return_value = None
            mock_mlflow.start_run.return_value.__enter__ = Mock(return_value=None)
            mock_mlflow.start_run.return_value.__exit__ = Mock(return_value=None)

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.return_value = "Integration test response"

                # Act
                result = chat_with_tracking(
                    model="gpt-4o",
                    prompt="Integration test prompt",
                    persona_id="integration_test",
                )

                # Assert
                assert result == "Integration test response"

                # Verify the complete MLflow flow
                mock_mlflow.set_experiment.assert_called()
                mock_mlflow.start_run.assert_called()
                mock_mlflow.log_params.assert_called()
                mock_mlflow.log_metrics.assert_called()
                mock_mlflow.end_run.assert_called()

    def test_multiple_sequential_calls(self):
        """Test that multiple sequential calls are tracked correctly."""
        # Arrange
        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                mock_chat.side_effect = ["Response 1", "Response 2", "Response 3"]

                # Act
                result1 = chat_with_tracking("gpt-4o", "Prompt 1", "persona_1")
                result2 = chat_with_tracking("gpt-3.5-turbo", "Prompt 2", "persona_2")
                result3 = chat_with_tracking("gpt-4", "Prompt 3", "persona_1")

                # Assert
                assert result1 == "Response 1"
                assert result2 == "Response 2"
                assert result3 == "Response 3"

                assert mock_tracker.track_llm_call.call_count == 3

                # Verify each call
                calls = mock_tracker.track_llm_call.call_args_list
                assert calls[0].kwargs["persona_id"] == "persona_1"
                assert calls[0].kwargs["model"] == "gpt-4o"
                assert calls[1].kwargs["persona_id"] == "persona_2"
                assert calls[1].kwargs["model"] == "gpt-3.5-turbo"
                assert calls[2].kwargs["persona_id"] == "persona_1"
                assert calls[2].kwargs["model"] == "gpt-4"

    def test_concurrent_tracking_isolation(self):
        """Test that concurrent calls don't interfere with each other."""
        # Arrange
        import threading
        from concurrent.futures import ThreadPoolExecutor

        with patch(
            "services.common.mlflow_openai_wrapper.MLflowExperimentTracker"
        ) as mock_tracker_class:
            mock_tracker = Mock()
            mock_tracker_class.return_value = mock_tracker

            from services.common.mlflow_openai_wrapper import chat_with_tracking

            with patch("services.common.openai_wrapper.chat") as mock_chat:
                # Each thread gets a unique response
                responses = {}

                def thread_specific_response(model, prompt):
                    thread_id = threading.current_thread().ident
                    response = f"Response for thread {thread_id}"
                    responses[thread_id] = (model, prompt, response)
                    return response

                mock_chat.side_effect = thread_specific_response

                # Act - Run multiple concurrent calls
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = []
                    for i in range(3):
                        future = executor.submit(
                            chat_with_tracking,
                            f"gpt-4o-{i}",
                            f"Prompt {i}",
                            f"persona_{i}",
                        )
                        futures.append(future)

                    # Wait for all to complete
                    results = [f.result() for f in futures]

                # Assert
                assert len(results) == 3
                assert mock_tracker.track_llm_call.call_count == 3

                # Verify each call has correct parameters
                for call in mock_tracker.track_llm_call.call_args_list:
                    kwargs = call.kwargs
                    assert kwargs["model"].startswith("gpt-4o-")
                    assert kwargs["prompt"].startswith("Prompt ")
                    assert kwargs["persona_id"].startswith("persona_")
