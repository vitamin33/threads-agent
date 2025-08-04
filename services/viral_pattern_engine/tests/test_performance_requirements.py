"""Performance tests for CRA-282 emotion trajectory mapping system.

Tests validate <300ms processing time requirement and system performance under various conditions.
"""

import pytest
import time
import threading
import queue
import statistics
from unittest.mock import patch
import psutil
import os

from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor
from services.viral_scraper.models import ViralPost
from datetime import datetime


class TestEmotionTrajectoryPerformance:
    """Performance test cases for emotion trajectory mapping system."""

    @pytest.fixture
    def emotion_analyzer(self):
        """Create emotion analyzer instance."""
        return EmotionAnalyzer()

    @pytest.fixture
    def trajectory_mapper(self):
        """Create trajectory mapper instance."""
        return TrajectoryMapper()

    @pytest.fixture
    def pattern_extractor(self):
        """Create pattern extractor instance."""
        return ViralPatternExtractor()

    @pytest.fixture
    def sample_contents(self):
        """Sample content variations for performance testing."""
        return [
            # Short content
            "Amazing discovery!",
            # Medium content
            "I'm so excited about this breakthrough! It's going to change everything we know.",
            # Long content with emotional complexity
            "I'm absolutely thrilled about this groundbreaking discovery! This could revolutionize "
            "our understanding of science. However, I'm also deeply concerned about the potential "
            "implications. What will this mean for society? I'm hopeful but cautious about the future.",
            # Very long content with multiple emotional shifts
            "This is incredible news that has me jumping for joy! I can't believe we've finally "
            "achieved this breakthrough after years of research. The implications are staggering! "
            "But wait, I'm starting to feel worried about how this might be misused. What if it "
            "falls into the wrong hands? The thought terrifies me. Actually, let me think about "
            "this more rationally. I trust that the scientific community will handle this responsibly. "
            "We have protocols and ethics committees for a reason. I'm feeling more confident now. "
            "This discovery gives me hope for solving many of humanity's greatest challenges. "
            "The future looks brighter than ever before!",
            # Complex emotional content
            "Mixed feelings about this announcement. Excited yet terrified. Hopeful but skeptical. "
            "Thrilled about the possibilities, worried about the risks. Amazing breakthrough, "
            "concerning implications. Revolutionary discovery, frightening consequences. "
            "Incredible achievement, terrifying potential. Wonderful news, scary future.",
            # Multilingual and special characters
            "¡Increíble! 🚀 Amazing discovery! 😍 But I'm worried... 😰 ¿Qué significa esto? "
            "This is FANTASTIC!!! 🎉🎊 However, je suis inquiet... 😟 Das ist wunderbar! 🌟",
        ]

    def test_emotion_analyzer_performance_requirement(
        self, emotion_analyzer, sample_contents
    ):
        """Test that emotion analysis meets <300ms requirement for all content types."""
        performance_results = []

        for i, content in enumerate(sample_contents):
            # Warm up (first run might be slower due to model loading)
            if i == 0:
                emotion_analyzer.analyze_emotions(content)

            # Actual performance test
            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(content)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            performance_results.append(
                {
                    "content_length": len(content),
                    "processing_time_ms": processing_time,
                    "content_type": f"sample_{i}",
                }
            )

            # Assert individual requirement
            assert processing_time < 300, (
                f"Content {i} took {processing_time:.2f}ms, expected <300ms"
            )

            # Verify result quality
            assert "emotions" in result
            assert len(result["emotions"]) == 8  # All 8 emotions
            assert result["confidence"] > 0.0

        # Overall performance statistics
        processing_times = [r["processing_time_ms"] for r in performance_results]
        avg_time = statistics.mean(processing_times)
        max_time = max(processing_times)
        min_time = min(processing_times)

        assert avg_time < 200, (
            f"Average processing time {avg_time:.2f}ms exceeds target of 200ms"
        )
        assert max_time < 300, (
            f"Maximum processing time {max_time:.2f}ms exceeds requirement"
        )

        print("\nEmotion Analyzer Performance Stats:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

    def test_trajectory_mapper_performance_requirement(self, trajectory_mapper):
        """Test that trajectory mapping meets <300ms requirement."""
        test_cases = [
            # Simple case
            ["I'm happy!", "This is great!"],
            # Medium complexity
            [
                "I'm excited about this!",
                "But I'm also worried.",
                "Actually, I think it'll be fine.",
            ],
            # High complexity
            [
                "Absolutely thrilled about this discovery!",
                "Wait, this could be dangerous...",
                "Actually, I'm terrified of the implications.",
                "But maybe we can use it for good?",
                "I'm feeling hopeful about the future.",
                "No, I'm still worried about the risks.",
                "Let's trust in our ability to handle this responsibly.",
            ],
            # Very high complexity
            [
                f"Segment {i}: I'm feeling emotional about this topic number {i}!"
                for i in range(20)
            ],
        ]

        performance_results = []

        for i, segments in enumerate(test_cases):
            start_time = time.time()
            result = trajectory_mapper.map_emotion_trajectory(segments)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            performance_results.append(
                {
                    "segment_count": len(segments),
                    "processing_time_ms": processing_time,
                    "case": f"test_case_{i}",
                }
            )

            # Assert individual requirement
            assert processing_time < 300, (
                f"Case {i} took {processing_time:.2f}ms, expected <300ms"
            )

            # Verify result quality
            assert "arc_type" in result
            assert "emotion_progression" in result
            assert len(result["emotion_progression"]) == len(segments)

        # Performance statistics
        processing_times = [r["processing_time_ms"] for r in performance_results]
        avg_time = statistics.mean(processing_times)

        assert avg_time < 200, (
            f"Average trajectory mapping time {avg_time:.2f}ms too high"
        )

        print("\nTrajectory Mapper Performance Stats:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Cases: {len(test_cases)}")

    def test_pattern_extractor_performance_requirement(self, pattern_extractor):
        """Test that complete pattern extraction meets <300ms requirement."""
        test_posts = [
            ViralPost(
                id="perf_post_1",
                content="Short and sweet!",
                author="@user1",
                engagement_metrics={
                    "likes": 100,
                    "shares": 10,
                    "comments": 5,
                    "views": 1000,
                },
                timestamp=datetime.utcnow().isoformat(),
                platform="threads",
            ),
            ViralPost(
                id="perf_post_2",
                content="I'm incredibly excited about this news! It's going to change everything. "
                "However, I'm also concerned about the implications.",
                author="@user2",
                engagement_metrics={
                    "likes": 500,
                    "shares": 50,
                    "comments": 25,
                    "views": 5000,
                },
                timestamp=datetime.utcnow().isoformat(),
                platform="threads",
            ),
            ViralPost(
                id="perf_post_3",
                content="This discovery is absolutely mind-blowing! I can't contain my excitement. "
                "The possibilities are endless and I'm thrilled about what this means for science. "
                "But I must admit, I'm also terrified about the potential for misuse. "
                "What if this technology ends up in the wrong hands? The thought keeps me awake at night. "
                "Still, I choose to remain optimistic. Humanity has always found ways to use "
                "breakthrough discoveries for the betterment of society. I trust we'll do the same here.",
                author="@user3",
                engagement_metrics={
                    "likes": 2000,
                    "shares": 300,
                    "comments": 150,
                    "views": 25000,
                },
                timestamp=datetime.utcnow().isoformat(),
                platform="threads",
            ),
        ]

        performance_results = []

        for i, post in enumerate(test_posts):
            start_time = time.time()
            patterns = pattern_extractor.extract_patterns(post)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            performance_results.append(
                {
                    "content_length": len(post.content),
                    "processing_time_ms": processing_time,
                    "post_id": post.id,
                }
            )

            # Assert individual requirement
            assert processing_time < 300, (
                f"Post {post.id} took {processing_time:.2f}ms, expected <300ms"
            )

            # Verify complete pattern extraction
            assert isinstance(patterns, dict)
            assert "pattern_strength" in patterns
            if len(post.content.split(".")) > 2:  # Multi-sentence content
                assert "emotion_trajectory" in patterns

        # Performance statistics
        processing_times = [r["processing_time_ms"] for r in performance_results]
        avg_time = statistics.mean(processing_times)

        assert avg_time < 250, (
            f"Average pattern extraction time {avg_time:.2f}ms too high"
        )

        print("\nPattern Extractor Performance Stats:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Posts processed: {len(test_posts)}")

    def test_concurrent_processing_performance(self, emotion_analyzer):
        """Test performance under concurrent processing load."""
        content = "I'm extremely excited about this breakthrough! But I'm also worried about the implications."
        num_threads = 10
        results_queue = queue.Queue()

        def process_emotion():
            """Process emotion analysis and record timing."""
            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(content)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            results_queue.put(
                {
                    "processing_time_ms": processing_time,
                    "success": "emotions" in result and len(result["emotions"]) == 8,
                }
            )

        # Create and start threads
        threads = []
        start_time = time.time()

        for _ in range(num_threads):
            thread = threading.Thread(target=process_emotion)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        total_time = (time.time() - start_time) * 1000

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == num_threads

        # All should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == num_threads, (
            f"Only {success_count}/{num_threads} succeeded"
        )

        # Individual processing times should still meet requirement
        processing_times = [r["processing_time_ms"] for r in results]
        max_individual_time = max(processing_times)
        avg_individual_time = statistics.mean(processing_times)

        assert max_individual_time < 400, (
            f"Max concurrent processing time {max_individual_time:.2f}ms too high"
        )
        assert avg_individual_time < 350, (
            f"Avg concurrent processing time {avg_individual_time:.2f}ms too high"
        )

        # Total wall-clock time should be reasonable
        assert total_time < 2000, (
            f"Total concurrent processing time {total_time:.2f}ms too high"
        )

        print("\nConcurrent Processing Performance:")
        print(f"  Threads: {num_threads}")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Avg individual: {avg_individual_time:.2f}ms")
        print(f"  Max individual: {max_individual_time:.2f}ms")

    def test_memory_efficiency_performance(self, emotion_analyzer):
        """Test memory efficiency during extended processing."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process many different content pieces
        content_templates = [
            "I'm excited about {}!",
            "This {} is amazing but concerning.",
            "Feeling happy about {} but worried about implications.",
        ]

        processing_times = []

        for i in range(100):
            content = content_templates[i % len(content_templates)].format(f"topic_{i}")

            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(content)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            processing_times.append(processing_time)

            # Verify result quality
            assert "emotions" in result
            assert result["confidence"] > 0.0

            # Check for memory leaks every 20 iterations
            if i > 0 and i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable
                assert memory_growth < 50, (
                    f"Memory leak detected: {memory_growth:.2f}MB growth at iteration {i}"
                )

        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_growth = final_memory - initial_memory

        # Performance should remain consistent
        avg_time = statistics.mean(processing_times)
        last_10_avg = statistics.mean(processing_times[-10:])
        first_10_avg = statistics.mean(processing_times[:10])

        time_degradation = abs(last_10_avg - first_10_avg)

        assert avg_time < 300, (
            f"Average processing time {avg_time:.2f}ms exceeds requirement"
        )
        assert time_degradation < 50, (
            f"Performance degraded by {time_degradation:.2f}ms over time"
        )
        assert total_memory_growth < 30, (
            f"Total memory growth {total_memory_growth:.2f}MB too high"
        )

        print("\nMemory Efficiency Performance:")
        print("  Iterations: 100")
        print(f"  Memory growth: {total_memory_growth:.2f}MB")
        print(f"  Avg processing time: {avg_time:.2f}ms")
        print(f"  Performance degradation: {time_degradation:.2f}ms")

    def test_large_content_performance_scaling(self, trajectory_mapper):
        """Test performance scaling with increasingly large content."""
        base_content = "I'm feeling emotional about this topic. "
        test_cases = []

        # Create content of varying lengths
        for multiplier in [1, 5, 10, 20, 50]:
            content = base_content * multiplier
            sentences = content.split(". ")
            test_cases.append(
                {
                    "segments": sentences,
                    "word_count": len(content.split()),
                    "multiplier": multiplier,
                }
            )

        performance_results = []

        for case in test_cases:
            start_time = time.time()
            result = trajectory_mapper.map_emotion_trajectory(case["segments"])
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            performance_results.append(
                {
                    "word_count": case["word_count"],
                    "multiplier": case["multiplier"],
                    "processing_time_ms": processing_time,
                    "segments": len(case["segments"]),
                }
            )

            # Verify result quality
            assert "arc_type" in result
            assert len(result["emotion_progression"]) == len(case["segments"])

        # Analyze scaling behavior
        for result in performance_results:
            word_count = result["word_count"]
            processing_time = result["processing_time_ms"]

            # Time per word should be reasonable
            time_per_word = processing_time / word_count
            assert time_per_word < 5.0, (
                f"Processing {time_per_word:.3f}ms per word is too slow"
            )

            # Even large content should complete within reasonable time
            if word_count > 200:
                assert processing_time < 500, (
                    f"Large content ({word_count} words) took {processing_time:.2f}ms"
                )
            else:
                assert processing_time < 300, (
                    f"Content ({word_count} words) took {processing_time:.2f}ms"
                )

        print("\nScaling Performance Results:")
        for result in performance_results:
            print(
                f"  {result['word_count']} words: {result['processing_time_ms']:.2f}ms "
                f"({result['processing_time_ms'] / result['word_count']:.3f}ms/word)"
            )

    def test_batch_processing_efficiency(self, pattern_extractor):
        """Test efficiency of batch processing multiple posts."""
        posts = []
        for i in range(20):
            content_length = [
                "Short post!",
                "Medium length post with some emotional content here.",
                "Long post with complex emotional journey that includes excitement, concern, hope, and resolution.",
            ][i % 3]

            posts.append(
                ViralPost(
                    id=f"batch_post_{i}",
                    content=content_length,
                    author=f"@user_{i}",
                    engagement_metrics={
                        "likes": 100 + i,
                        "shares": 10 + i,
                        "comments": 5 + i,
                        "views": 1000 + i * 100,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                    platform="threads",
                )
            )

        # Test individual processing
        individual_times = []
        for post in posts:
            start_time = time.time()
            patterns = pattern_extractor.extract_patterns(post)
            end_time = time.time()

            individual_times.append((end_time - start_time) * 1000)
            assert isinstance(patterns, dict)

        total_individual_time = sum(individual_times)
        avg_individual_time = statistics.mean(individual_times)

        # Verify batch efficiency
        assert avg_individual_time < 300, (
            f"Average individual processing {avg_individual_time:.2f}ms too high"
        )
        assert total_individual_time < 4000, (
            f"Total batch processing {total_individual_time:.2f}ms too high"
        )

        print("\nBatch Processing Efficiency:")
        print(f"  Posts: {len(posts)}")
        print(f"  Total time: {total_individual_time:.2f}ms")
        print(f"  Average per post: {avg_individual_time:.2f}ms")
        print(f"  Posts per second: {1000 * len(posts) / total_individual_time:.2f}")

    def test_error_handling_performance_impact(self, emotion_analyzer):
        """Test that error handling doesn't significantly impact performance."""
        # Test normal processing
        normal_content = "I'm excited about this development!"
        normal_times = []

        for _ in range(10):
            start_time = time.time()
            emotion_analyzer.analyze_emotions(normal_content)
            end_time = time.time()
            normal_times.append((end_time - start_time) * 1000)

        avg_normal_time = statistics.mean(normal_times)

        # Test error-prone processing
        error_contents = [
            "",  # Empty content
            "   \n\t  ",  # Whitespace only
            "!!!" * 100,  # Repetitive punctuation
            "🎉" * 50,  # Emoji overload
        ]

        error_times = []
        for content in error_contents:
            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(content)
            end_time = time.time()

            error_times.append((end_time - start_time) * 1000)
            # Should still return valid result structure
            assert "emotions" in result

        avg_error_time = statistics.mean(error_times)

        # Error handling shouldn't be significantly slower
        performance_impact = avg_error_time - avg_normal_time
        assert performance_impact < 100, (
            f"Error handling adds {performance_impact:.2f}ms overhead"
        )
        assert avg_error_time < 400, (
            f"Error case processing {avg_error_time:.2f}ms too slow"
        )

        print("\nError Handling Performance Impact:")
        print(f"  Normal processing: {avg_normal_time:.2f}ms")
        print(f"  Error case processing: {avg_error_time:.2f}ms")
        print(f"  Performance impact: {performance_impact:.2f}ms")

    @patch("services.viral_pattern_engine.emotion_analyzer.MODELS_AVAILABLE", False)
    def test_fallback_mode_performance(self, emotion_analyzer):
        """Test performance when using fallback keyword analysis."""
        test_contents = [
            "I'm excited and happy about this!",
            "This is terrible and makes me sad.",
            "I'm angry and frustrated with this situation.",
            "Surprisingly good news that I trust completely.",
        ]

        fallback_times = []

        for content in test_contents:
            start_time = time.time()
            result = emotion_analyzer.analyze_emotions(content)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            fallback_times.append(processing_time)

            # Verify fallback mode is working
            assert result["model_info"]["bert_model"] == "keyword-fallback"
            assert result["confidence"] == 0.7  # Fallback confidence
            assert "emotions" in result
            assert len(result["emotions"]) == 8

        avg_fallback_time = statistics.mean(fallback_times)
        max_fallback_time = max(fallback_times)

        # Fallback mode should be even faster
        assert avg_fallback_time < 50, (
            f"Fallback mode too slow: {avg_fallback_time:.2f}ms"
        )
        assert max_fallback_time < 100, (
            f"Max fallback time too slow: {max_fallback_time:.2f}ms"
        )

        print("\nFallback Mode Performance:")
        print(f"  Average: {avg_fallback_time:.2f}ms")
        print(f"  Maximum: {max_fallback_time:.2f}ms")

    def test_performance_regression_detection(
        self, emotion_analyzer, trajectory_mapper
    ):
        """Test for performance regression detection."""
        # Baseline performance expectations
        BASELINE_EMOTION_ANALYSIS = 200  # ms
        BASELINE_TRAJECTORY_MAPPING = 150  # ms

        # Test emotion analysis performance
        content = "I'm thrilled about this discovery but concerned about implications."
        emotion_times = []

        for _ in range(5):
            start_time = time.time()
            emotion_analyzer.analyze_emotions(content)
            end_time = time.time()
            emotion_times.append((end_time - start_time) * 1000)

        avg_emotion_time = statistics.mean(emotion_times)

        # Test trajectory mapping performance
        segments = ["I'm excited!", "But worried.", "Actually optimistic."]
        trajectory_times = []

        for _ in range(5):
            start_time = time.time()
            trajectory_mapper.map_emotion_trajectory(segments)
            end_time = time.time()
            trajectory_times.append((end_time - start_time) * 1000)

        avg_trajectory_time = statistics.mean(trajectory_times)

        # Check for regression
        emotion_regression = (
            avg_emotion_time - BASELINE_EMOTION_ANALYSIS
        ) / BASELINE_EMOTION_ANALYSIS
        trajectory_regression = (
            avg_trajectory_time - BASELINE_TRAJECTORY_MAPPING
        ) / BASELINE_TRAJECTORY_MAPPING

        # Allow 20% performance regression threshold
        assert emotion_regression < 0.20, (
            f"Emotion analysis regression: {emotion_regression:.2%}"
        )
        assert trajectory_regression < 0.20, (
            f"Trajectory mapping regression: {trajectory_regression:.2%}"
        )

        # Still must meet hard requirements
        assert avg_emotion_time < 300, (
            f"Emotion analysis {avg_emotion_time:.2f}ms exceeds requirement"
        )
        assert avg_trajectory_time < 300, (
            f"Trajectory mapping {avg_trajectory_time:.2f}ms exceeds requirement"
        )

        print("\nPerformance Regression Check:")
        print(
            f"  Emotion analysis: {avg_emotion_time:.2f}ms (baseline: {BASELINE_EMOTION_ANALYSIS}ms)"
        )
        print(
            f"  Trajectory mapping: {avg_trajectory_time:.2f}ms (baseline: {BASELINE_TRAJECTORY_MAPPING}ms)"
        )
        print(f"  Emotion regression: {emotion_regression:.2%}")
        print(f"  Trajectory regression: {trajectory_regression:.2%}")

    def test_warm_up_vs_steady_state_performance(self, emotion_analyzer):
        """Test performance difference between cold start and steady state."""
        content = "This is amazing but also concerning news!"

        # Cold start (first run)
        start_time = time.time()
        emotion_analyzer.analyze_emotions(content)
        cold_start_time = (time.time() - start_time) * 1000

        # Warm up runs
        for _ in range(5):
            emotion_analyzer.analyze_emotions(content)

        # Steady state runs
        steady_state_times = []
        for _ in range(10):
            start_time = time.time()
            emotion_analyzer.analyze_emotions(content)
            end_time = time.time()
            steady_state_times.append((end_time - start_time) * 1000)

        avg_steady_state = statistics.mean(steady_state_times)

        # Steady state should be faster than cold start
        performance_improvement = cold_start_time - avg_steady_state

        # Both should meet requirements
        assert cold_start_time < 500, f"Cold start {cold_start_time:.2f}ms too slow"
        assert avg_steady_state < 300, (
            f"Steady state {avg_steady_state:.2f}ms exceeds requirement"
        )

        print("\nWarm-up vs Steady State Performance:")
        print(f"  Cold start: {cold_start_time:.2f}ms")
        print(f"  Steady state avg: {avg_steady_state:.2f}ms")
        print(f"  Performance improvement: {performance_improvement:.2f}ms")
