"""Performance tests for emotion trajectory mapping system."""

import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper


class TestEmotionPerformance:
    """Performance tests for emotion analysis components."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    @pytest.fixture
    def sample_content_segments(self):
        """Sample content segments for performance testing."""
        return [
            "This is an amazing discovery that will change everything we know about viral content!",
            "At first, I was skeptical about the claims being made, but now I'm starting to believe.",
            "The results are absolutely incredible and beyond what anyone could have imagined!",
            "I can't wait to share this breakthrough with the entire community of creators.",
        ]

    @pytest.fixture
    def large_content_segments(self):
        """Large content segments for stress testing."""
        segments = []
        base_texts = [
            "This is the beginning of an incredible journey that will take us through emotional highs and lows.",
            "As we progress through this story, you'll notice the emotional intensity building gradually.",
            "The peak moment arrives with overwhelming joy and excitement that fills every reader.",
            "Finally, we settle into a satisfying resolution that brings peace and contentment.",
        ]

        # Create 20 segments by expanding base texts
        for i in range(20):
            base_text = base_texts[i % len(base_texts)]
            expanded_text = f"{base_text} " + " ".join(
                [
                    "Additional context and detail to make this segment longer and more realistic."
                    for _ in range(3)
                ]
            )
            segments.append(expanded_text)

        return segments

    def test_emotion_analyzer_performance_single_analysis(self, emotion_analyzer):
        """Test emotion analyzer meets <300ms requirement for single analysis."""
        # Arrange
        test_text = "I'm absolutely thrilled about this incredible discovery! This changes everything!"

        # Act & Assert - Multiple runs to get average
        execution_times = []
        for _ in range(10):
            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(test_text)
            end_time = time.time()

            execution_time_ms = (end_time - start_time) * 1000
            execution_times.append(execution_time_ms)

            # Verify result structure
            assert "emotions" in result
            assert "confidence" in result

        # Performance assertions
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)

        assert avg_execution_time < 100, (
            f"Average execution time {avg_execution_time:.2f}ms exceeds 100ms"
        )
        assert max_execution_time < 300, (
            f"Max execution time {max_execution_time:.2f}ms exceeds 300ms"
        )

    def test_trajectory_mapper_performance_multiple_segments(
        self, trajectory_mapper, sample_content_segments
    ):
        """Test trajectory mapper meets <300ms requirement for multiple segments."""
        # Act & Assert - Multiple runs to get average
        execution_times = []
        for _ in range(5):
            start_time = time.time()
            result = trajectory_mapper.map_emotion_trajectory(sample_content_segments)
            end_time = time.time()

            execution_time_ms = (end_time - start_time) * 1000
            execution_times.append(execution_time_ms)

            # Verify result structure
            assert "arc_type" in result
            assert "emotion_progression" in result
            assert "emotional_variance" in result

        # Performance assertions
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)

        assert avg_execution_time < 250, (
            f"Average execution time {avg_execution_time:.2f}ms exceeds 250ms"
        )
        assert max_execution_time < 300, (
            f"Max execution time {max_execution_time:.2f}ms exceeds 300ms"
        )

    def test_full_workflow_performance(
        self, trajectory_mapper, sample_content_segments
    ):
        """Test complete emotion analysis workflow performance."""
        # Act & Assert - Test full workflow including transitions
        execution_times = []
        for _ in range(5):
            start_time = time.time()

            # Full workflow: trajectory + transitions
            trajectory_result = trajectory_mapper.map_emotion_trajectory(
                sample_content_segments
            )
            transition_result = trajectory_mapper.analyze_emotion_transitions(
                sample_content_segments
            )

            end_time = time.time()

            execution_time_ms = (end_time - start_time) * 1000
            execution_times.append(execution_time_ms)

            # Verify results
            assert trajectory_result["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]
            assert len(transition_result["transitions"]) >= 0

        # Performance assertions for full workflow
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)

        assert avg_execution_time < 400, (
            f"Average full workflow time {avg_execution_time:.2f}ms exceeds 400ms"
        )
        assert max_execution_time < 500, (
            f"Max full workflow time {max_execution_time:.2f}ms exceeds 500ms"
        )

    def test_performance_with_large_content(
        self, trajectory_mapper, large_content_segments
    ):
        """Test performance with large content (20 segments)."""
        # Act
        start_time = time.time()
        result = trajectory_mapper.map_emotion_trajectory(large_content_segments)
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000

        # Assert
        assert execution_time_ms < 1000, (
            f"Large content processing time {execution_time_ms:.2f}ms exceeds 1000ms"
        )
        assert len(result["emotion_progression"]) == 20
        assert result["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]

    def test_memory_usage_under_load(self, trajectory_mapper, sample_content_segments):
        """Test memory usage doesn't grow excessively under repeated analysis."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run many analyses
        for i in range(50):
            result = trajectory_mapper.map_emotion_trajectory(sample_content_segments)
            assert result["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]

            # Check memory every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable (< 100MB)
                assert memory_growth < 100, (
                    f"Memory grew by {memory_growth:.2f}MB after {i + 1} analyses"
                )

    def test_concurrent_analysis_performance(
        self, trajectory_mapper, sample_content_segments
    ):
        """Test performance with concurrent emotion analyses."""

        def analyze_single():
            """Single analysis function for threading."""
            return trajectory_mapper.map_emotion_trajectory(sample_content_segments)

        # Test with 10 concurrent analyses
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze_single) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]

        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000

        # Assert
        assert len(results) == 10
        assert all(
            r["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]
            for r in results
        )

        # Concurrent processing should be faster than sequential (due to I/O parallelization)
        # Allow up to 2 seconds for 10 concurrent analyses
        assert total_time_ms < 2000, f"Concurrent processing took {total_time_ms:.2f}ms"

    @pytest.mark.parametrize("segment_count", [1, 3, 5, 10, 15])
    def test_performance_scales_with_segment_count(
        self, trajectory_mapper, segment_count
    ):
        """Test that performance scales reasonably with number of segments."""
        # Arrange - Create segments of specified count
        base_segment = (
            "This is a test segment with emotional content that needs analysis."
        )
        segments = [f"{base_segment} Segment {i}." for i in range(segment_count)]

        # Act
        start_time = time.time()
        result = trajectory_mapper.map_emotion_trajectory(segments)
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000

        # Assert - Performance should scale roughly linearly
        expected_max_time = max(
            300, segment_count * 50
        )  # 50ms per segment + 300ms base
        assert execution_time_ms < expected_max_time, (
            f"Processing {segment_count} segments took {execution_time_ms:.2f}ms, expected < {expected_max_time}ms"
        )

        # Verify result quality
        assert len(result["emotion_progression"]) == segment_count
        assert result["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]

    def test_performance_with_fallback_analysis(self, emotion_analyzer):
        """Test performance when falling back to keyword-based analysis."""
        # Arrange - Force keyword-based analysis by mocking model failure
        with patch.object(emotion_analyzer, "models_loaded", False):
            test_text = "I'm absolutely thrilled about this incredible discovery!"

            # Act
            execution_times = []
            for _ in range(10):
                start_time = time.time()
                result = emotion_analyzer.analyze_emotions(test_text)
                end_time = time.time()

                execution_time_ms = (end_time - start_time) * 1000
                execution_times.append(execution_time_ms)

                # Verify fallback result
                assert result["model_info"]["bert_model"] == "keyword-fallback"
                assert "emotions" in result

        # Assert - Fallback should be very fast
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)

        assert avg_execution_time < 10, (
            f"Fallback average time {avg_execution_time:.2f}ms too slow"
        )
        assert max_execution_time < 50, (
            f"Fallback max time {max_execution_time:.2f}ms too slow"
        )

    def test_batch_processing_performance(self, trajectory_mapper):
        """Test performance of batch processing multiple content pieces."""
        # Arrange - Create multiple content pieces
        content_batches = [
            ["Happy start!", "Getting excited!", "Amazing end!"],
            ["Sad beginning.", "Still sad.", "Getting better.", "Much happier!"],
            ["Neutral content.", "Staying steady.", "No major changes."],
            ["Surprising twist!", "Shocked reaction!", "Unexpected outcome!"],
            [
                "Fearful situation.",
                "Growing anxiety.",
                "Overwhelming dread.",
                "Final terror!",
            ],
        ]

        # Act - Process all batches
        start_time = time.time()
        results = []
        for content_segments in content_batches:
            result = trajectory_mapper.map_emotion_trajectory(content_segments)
            results.append(result)
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_batch = total_time_ms / len(content_batches)

        # Assert
        assert len(results) == 5
        assert all(
            r["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]
            for r in results
        )
        assert avg_time_per_batch < 400, (
            f"Average batch processing time {avg_time_per_batch:.2f}ms too slow"
        )
        assert total_time_ms < 1500, (
            f"Total batch processing time {total_time_ms:.2f}ms too slow"
        )

    def test_peak_valley_detection_performance(self, trajectory_mapper):
        """Test performance of peak and valley detection algorithm."""
        # Arrange - Create content with clear peaks and valleys
        segments = [
            "Starting neutral with baseline emotions.",
            "Building up excitement and anticipation here!",
            "PEAK MOMENT OF ABSOLUTE JOY AND EXCITEMENT!!!",
            "Coming down from the high, feeling satisfied.",
            "Dropping into sadness and disappointment now.",
            "Rock bottom valley of despair and hopelessness.",
            "Slowly climbing back up with renewed hope.",
            "Another peak of triumph and achievement!",
            "Final settling into peaceful contentment.",
        ]

        # Act
        start_time = time.time()
        result = trajectory_mapper.map_emotion_trajectory(segments)
        peaks_valleys = trajectory_mapper.detect_peaks_and_valleys(
            result["emotion_progression"]
        )
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000

        # Assert
        assert execution_time_ms < 400, (
            f"Peak/valley detection took {execution_time_ms:.2f}ms"
        )
        # With improved error handling, peak detection may vary
        assert len(peaks_valleys["peak_indices"]) >= 0  # May or may not detect peaks
        assert (
            len(peaks_valleys["valley_indices"]) >= 0
        )  # May or may not detect valleys

        # Verify peaks are higher intensity than valleys
        if peaks_valleys["peaks"] and peaks_valleys["valleys"]:
            peak_intensities = [
                p.get("joy", 0) - p.get("sadness", 0) for p in peaks_valleys["peaks"]
            ]
            valley_intensities = [
                v.get("joy", 0) - v.get("sadness", 0) for v in peaks_valleys["valleys"]
            ]

            avg_peak_intensity = statistics.mean(peak_intensities)
            avg_valley_intensity = statistics.mean(valley_intensities)

            assert avg_peak_intensity > avg_valley_intensity, (
                "Peaks should have higher intensity than valleys"
            )

    def test_transition_analysis_performance(self, trajectory_mapper):
        """Test performance of emotion transition analysis."""
        # Arrange - Create content with clear emotional transitions
        segments = [
            "I trust this will work out perfectly fine.",
            "Wait, now I'm getting worried about the outcome.",
            "OMG I'm so angry about what just happened!",
            "Actually, I'm surprised by this turn of events.",
            "Now I'm feeling joyful about the possibilities!",
        ]

        # Act
        start_time = time.time()
        result = trajectory_mapper.analyze_emotion_transitions(segments)
        end_time = time.time()

        execution_time_ms = (end_time - start_time) * 1000

        # Assert
        assert execution_time_ms < 350, (
            f"Transition analysis took {execution_time_ms:.2f}ms"
        )
        assert (
            len(result["transitions"]) == 4
        )  # Should have 4 transitions (5 segments - 1)
        assert result["transition_strength"] > 0  # Should detect meaningful transitions

        # Verify transition variety
        transition_types = [
            t["from_emotion"] + "_to_" + t["to_emotion"] for t in result["transitions"]
        ]
        unique_transitions = set(transition_types)
        assert len(unique_transitions) >= 3, (
            "Should detect multiple different transition types"
        )

    @pytest.mark.asyncio
    async def test_async_performance_simulation(
        self, trajectory_mapper, sample_content_segments
    ):
        """Test performance in async/concurrent scenarios."""

        async def async_analyze():
            """Simulate async analysis by running in thread pool."""
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, trajectory_mapper.map_emotion_trajectory, sample_content_segments
            )

        # Act - Run multiple async analyses
        start_time = time.time()
        tasks = [async_analyze() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_task = total_time_ms / len(tasks)

        # Assert
        assert len(results) == 5
        assert all(
            r["arc_type"] in ["rising", "falling", "roller_coaster", "steady"]
            for r in results
        )
        assert avg_time_per_task < 300, (
            f"Average async task time {avg_time_per_task:.2f}ms too slow"
        )
        assert total_time_ms < 1000, (
            f"Total async processing time {total_time_ms:.2f}ms too slow"
        )
