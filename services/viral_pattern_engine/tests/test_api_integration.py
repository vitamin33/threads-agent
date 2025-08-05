"""API integration tests for CRA-282 emotion trajectory mapping endpoints."""

import pytest
import time
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from services.viral_pattern_engine.main import app
from services.viral_scraper.models import ViralPost


class TestEmotionTrajectoryAPIIntegration:
    """Test cases for emotion trajectory API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_viral_post(self):
        """Sample viral post for testing."""
        return ViralPost(
            id="test_post_12345",
            content="I'm absolutely thrilled about this groundbreaking discovery! "
            "It's going to revolutionize everything we know. "
            "But I'm also concerned about the potential implications and risks. "
            "What does this mean for our future?",
            author="@tech_expert",
            engagement_metrics={
                "likes": 1500,
                "shares": 300,
                "comments": 85,
                "views": 50000,
            },
            timestamp=datetime.utcnow().isoformat(),
            platform="threads",
        )

    @pytest.fixture
    def sample_short_post(self):
        """Sample short post for testing."""
        return ViralPost(
            id="short_post_123",
            content="Amazing discovery!",
            author="@researcher",
            engagement_metrics={
                "likes": 100,
                "shares": 20,
                "comments": 5,
                "views": 2000,
            },
            timestamp=datetime.utcnow().isoformat(),
            platform="threads",
        )

    def test_extract_patterns_includes_emotion_trajectory(
        self, client, sample_viral_post
    ):
        """Test that extract-patterns endpoint includes emotion trajectory analysis."""
        # Arrange
        post_data = sample_viral_post.dict()

        # Act
        response = client.post("/extract-patterns", json=post_data)

        # Assert
        assert response.status_code == 200
        patterns = response.json()

        # Should include emotion trajectory for longer content
        assert "emotion_trajectory" in patterns

        trajectory = patterns["emotion_trajectory"]
        assert "arc_type" in trajectory
        assert "emotion_progression" in trajectory
        assert "peak_segments" in trajectory
        assert "valley_segments" in trajectory
        assert "emotional_variance" in trajectory

        # Arc type should be one of the valid types
        valid_arc_types = ["rising", "falling", "roller_coaster", "steady"]
        assert trajectory["arc_type"] in valid_arc_types

        # Emotional variance should be a valid float
        assert isinstance(trajectory["emotional_variance"], float)
        assert 0.0 <= trajectory["emotional_variance"] <= 1.0

    def test_extract_patterns_performance_requirement(self, client, sample_viral_post):
        """Test that emotion trajectory analysis meets <300ms performance requirement."""
        # Arrange
        post_data = sample_viral_post.dict()

        # Act - Measure response time
        start_time = time.time()
        response = client.post("/extract-patterns", json=post_data)
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        # Assert
        assert response.status_code == 200
        assert response_time_ms < 300, (
            f"Response took {response_time_ms:.2f}ms, expected <300ms"
        )

        # Should still return valid emotion trajectory
        patterns = response.json()
        assert "emotion_trajectory" in patterns

    def test_extract_patterns_with_short_content(self, client, sample_short_post):
        """Test emotion trajectory analysis with short content."""
        # Arrange
        post_data = sample_short_post.dict()

        # Act
        response = client.post("/extract-patterns", json=post_data)

        # Assert
        assert response.status_code == 200
        patterns = response.json()

        # Short content might still have emotion_trajectory but with limited analysis
        if "emotion_trajectory" in patterns:
            trajectory = patterns["emotion_trajectory"]
            # Should handle short content gracefully
            assert "arc_type" in trajectory
            # Arc type might be "steady" for very short content
            assert trajectory["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]

    def test_extract_patterns_with_mixed_emotions(self, client):
        """Test emotion trajectory with complex mixed emotional content."""
        # Arrange
        complex_post = {
            "id": "complex_post_456",
            "content": "I'm so excited about winning this award! It's a dream come true. "
            "However, I'm terrified about the responsibility that comes with it. "
            "What if I can't live up to expectations? But then again, I'm grateful "
            "for this opportunity to make a difference. I trust that everything "
            "will work out for the best.",
            "author": "@award_winner",
            "engagement_metrics": {
                "likes": 800,
                "shares": 150,
                "comments": 45,
                "views": 25000,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        # Act
        response = client.post("/extract-patterns", json=complex_post)

        # Assert
        assert response.status_code == 200
        patterns = response.json()
        assert "emotion_trajectory" in patterns

        trajectory = patterns["emotion_trajectory"]

        # Should detect roller coaster pattern due to mixed emotions
        assert trajectory["arc_type"] in ["roller_coaster", "rising", "falling"]

        # Should have emotional variance due to mixed emotions
        assert trajectory["emotional_variance"] > 0.3

        # Should detect multiple emotion segments
        assert len(trajectory["emotion_progression"]) >= 3

    def test_extract_patterns_handles_unicode_content(self, client):
        """Test emotion trajectory with Unicode and emoji content."""
        # Arrange
        unicode_post = {
            "id": "unicode_post_789",
            "content": "🎉 Je suis très heureux! This is amazing! 😍 "
            "But I'm also worried about the future... 😰 "
            "¿Qué pasará después? 🤔 I hope everything works out! 🙏",
            "author": "@global_user",
            "engagement_metrics": {
                "likes": 500,
                "shares": 80,
                "comments": 25,
                "views": 15000,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        # Act
        response = client.post("/extract-patterns", json=unicode_post)

        # Assert
        assert response.status_code == 200
        patterns = response.json()

        # Should handle Unicode content without errors
        assert "emotion_trajectory" in patterns
        trajectory = patterns["emotion_trajectory"]
        assert trajectory["arc_type"] in [
            "rising",
            "falling",
            "roller_coaster",
            "steady",
        ]

    def test_analyze_batch_includes_emotion_trajectories(
        self, client, sample_viral_post, sample_short_post
    ):
        """Test batch analysis includes emotion trajectory data in summary."""
        # Arrange
        batch_request = {
            "posts": [
                sample_viral_post.dict(),
                sample_short_post.dict(),
                {
                    "id": "batch_post_3",
                    "content": "This is moderately exciting news that brings hope for the future. "
                    "I'm cautiously optimistic about what's to come.",
                    "author": "@optimist",
                    "engagement_metrics": {
                        "likes": 200,
                        "shares": 30,
                        "comments": 10,
                        "views": 8000,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": "threads",
                },
            ]
        }

        # Act
        response = client.post("/analyze-batch", json=batch_request)

        # Assert
        assert response.status_code == 200
        batch_result = response.json()

        assert "results" in batch_result
        assert "summary" in batch_result
        assert len(batch_result["results"]) == 3

        # Each result should include emotion trajectory
        for result in batch_result["results"]:
            if "emotion_trajectory" in result:
                trajectory = result["emotion_trajectory"]
                assert "arc_type" in trajectory
                assert "emotional_variance" in trajectory

        # Summary should include aggregated metrics
        summary = batch_result["summary"]
        assert "total_posts" in summary
        assert summary["total_posts"] == 3

    def test_extract_patterns_error_handling(self, client):
        """Test API error handling for invalid requests."""
        # Test with invalid post data
        invalid_post = {
            "id": "invalid_post",
            # Missing required content field
            "author": "@test",
            "engagement_metrics": {},
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        response = client.post("/extract-patterns", json=invalid_post)
        assert response.status_code == 422  # Validation error

        # Test with empty content
        empty_content_post = {
            "id": "empty_post",
            "content": "",
            "author": "@test",
            "engagement_metrics": {},
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        response = client.post("/extract-patterns", json=empty_content_post)
        # Should handle gracefully but might return different patterns
        if response.status_code == 200:
            patterns = response.json()
            # Should not crash, but emotion trajectory might be minimal
            assert isinstance(patterns, dict)

    def test_health_endpoint_availability(self, client):
        """Test health check endpoint is available."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "viral_pattern_engine"

    def test_pattern_types_includes_emotion_patterns(self, client):
        """Test pattern-types endpoint includes emotion-related patterns."""
        # Act
        response = client.get("/pattern-types")

        # Assert
        assert response.status_code == 200
        pattern_types = response.json()

        assert "emotion_patterns" in pattern_types
        emotion_patterns = pattern_types["emotion_patterns"]

        # Should include basic emotion types
        expected_emotions = ["excitement", "amazement", "surprise"]
        for emotion in expected_emotions:
            assert emotion in emotion_patterns

    @patch("services.viral_pattern_engine.pattern_extractor.ViralPatternExtractor")
    def test_extract_patterns_handles_extractor_failure(
        self, mock_extractor, client, sample_viral_post
    ):
        """Test API gracefully handles pattern extraction failures."""
        # Arrange
        mock_instance = MagicMock()
        mock_instance.extract_patterns.side_effect = Exception("Model loading failed")
        mock_extractor.return_value = mock_instance

        post_data = sample_viral_post.dict()

        # Act
        response = client.post("/extract-patterns", json=post_data)

        # Assert
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data
        assert "Pattern extraction failed" in error_data["detail"]

    def test_concurrent_requests_performance(self, client, sample_viral_post):
        """Test performance under concurrent requests."""
        import threading
        import queue

        post_data = sample_viral_post.dict()
        results_queue = queue.Queue()
        num_threads = 5

        def make_request():
            """Make a request and record the result."""
            start_time = time.time()
            response = client.post("/extract-patterns", json=post_data)
            end_time = time.time()

            results_queue.put(
                {
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "has_trajectory": "emotion_trajectory" in response.json()
                    if response.status_code == 200
                    else False,
                }
            )

        # Create and start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Assert
        assert len(results) == num_threads

        # All requests should succeed
        for result in results:
            assert result["status_code"] == 200
            assert result["has_trajectory"] is True
            assert result["response_time"] < 500  # Should be reasonable under load

        # Average response time should still be good
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 350, (
            f"Average response time {avg_response_time:.2f}ms too high"
        )

    def test_large_content_processing(self, client):
        """Test emotion trajectory processing with large content."""
        # Arrange - Create large content with multiple segments
        large_content = (
            "I'm incredibly excited about this groundbreaking discovery! "
            "This could change everything we know about science. "
            * 10
            + "However, I'm deeply concerned about the ethical implications. "
            "What will this mean for society? "
            * 10
            + "But then again, I'm hopeful that we can use this responsibly. "
            "The future looks bright if we proceed carefully. " * 10
        )

        large_post = {
            "id": "large_post_999",
            "content": large_content,
            "author": "@researcher",
            "engagement_metrics": {
                "likes": 2000,
                "shares": 500,
                "comments": 150,
                "views": 100000,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        # Act
        start_time = time.time()
        response = client.post("/extract-patterns", json=large_post)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000

        # Assert
        assert response.status_code == 200
        assert processing_time < 500, (
            f"Large content processing took {processing_time:.2f}ms"
        )

        patterns = response.json()
        assert "emotion_trajectory" in patterns

        trajectory = patterns["emotion_trajectory"]
        # Should detect complex emotional pattern
        assert trajectory["emotional_variance"] > 0.4
        assert len(trajectory["emotion_progression"]) >= 10  # Multiple segments

    def test_extract_patterns_memory_efficiency(self, client):
        """Test memory efficiency during emotion trajectory processing."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple posts
        for i in range(20):
            post_data = {
                "id": f"memory_test_post_{i}",
                "content": f"This is test post number {i} with emotional content. "
                f"I'm feeling excited about test {i}! But also worried about performance. "
                f"Will this consume too much memory? I hope not! " * 5,
                "author": f"@user_{i}",
                "engagement_metrics": {
                    "likes": 100 + i,
                    "shares": 10 + i,
                    "comments": 5 + i,
                    "views": 1000 + i * 100,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            }

            response = client.post("/extract-patterns", json=post_data)
            assert response.status_code == 200

        # Check final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable
        assert memory_growth < 50, f"Memory growth {memory_growth:.2f}MB too high"

    def test_analyze_batch_performance_with_emotion_trajectories(self, client):
        """Test batch analysis performance with emotion trajectory processing."""
        # Arrange - Create batch of posts with varying complexity
        posts = []
        for i in range(10):
            content_variations = [
                "Simple happy content!",
                "I'm excited but also worried about this development. It's amazing but scary.",
                "This is incredible news! However, I'm concerned about the implications. "
                "What does this mean for our future? I'm hopeful but cautious.",
                "Absolutely thrilled! But terrified. Amazing discovery! Concerning implications. "
                "Hopeful future! Uncertain times ahead!",
            ]

            post = {
                "id": f"batch_perf_post_{i}",
                "content": content_variations[i % len(content_variations)],
                "author": f"@batch_user_{i}",
                "engagement_metrics": {
                    "likes": 100 + i * 20,
                    "shares": 10 + i * 5,
                    "comments": 5 + i * 2,
                    "views": 1000 + i * 500,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "platform": "threads",
            }
            posts.append(post)

        batch_request = {"posts": posts}

        # Act
        start_time = time.time()
        response = client.post("/analyze-batch", json=batch_request)
        end_time = time.time()

        processing_time = (end_time - start_time) * 1000

        # Assert
        assert response.status_code == 200
        assert processing_time < 2000, (
            f"Batch processing took {processing_time:.2f}ms, expected <2000ms"
        )

        batch_result = response.json()
        assert len(batch_result["results"]) == 10

        # Verify emotion trajectories are included where applicable
        trajectory_count = sum(
            1 for result in batch_result["results"] if "emotion_trajectory" in result
        )
        assert trajectory_count >= 5  # At least half should have trajectories

    def test_api_response_schema_validation(self, client, sample_viral_post):
        """Test that API responses conform to expected schema."""
        # Act
        response = client.post("/extract-patterns", json=sample_viral_post.dict())

        # Assert
        assert response.status_code == 200
        patterns = response.json()

        # Validate emotion trajectory schema
        if "emotion_trajectory" in patterns:
            trajectory = patterns["emotion_trajectory"]

            # Required fields
            required_fields = [
                "arc_type",
                "emotion_progression",
                "peak_segments",
                "valley_segments",
                "emotional_variance",
            ]
            for field in required_fields:
                assert field in trajectory, f"Missing required field: {field}"

            # Data types
            assert isinstance(trajectory["arc_type"], str)
            assert isinstance(trajectory["emotion_progression"], list)
            assert isinstance(trajectory["peak_segments"], list)
            assert isinstance(trajectory["valley_segments"], list)
            assert isinstance(trajectory["emotional_variance"], (int, float))

            # Value ranges
            assert trajectory["emotional_variance"] >= 0.0
            assert trajectory["emotional_variance"] <= 1.0

            # Each emotion progression item should have emotion scores
            for emotion_segment in trajectory["emotion_progression"]:
                assert isinstance(emotion_segment, dict)
                emotion_keys = [
                    "joy",
                    "anger",
                    "fear",
                    "sadness",
                    "surprise",
                    "disgust",
                    "trust",
                    "anticipation",
                ]
                for emotion in emotion_keys:
                    if emotion in emotion_segment:
                        assert 0.0 <= emotion_segment[emotion] <= 1.0

    def test_extract_patterns_with_special_characters(self, client):
        """Test emotion trajectory with special characters and formatting."""
        # Arrange
        special_post = {
            "id": "special_char_post",
            "content": "OMG!!! This is AMAZING 🚀🚀🚀 #breakthrough #science "
            "But wait... there's more!!! 😱😱😱 "
            "Actually, I'm kinda worried now 😰😰😰 "
            "Nevermind, it's all good! 😊✨🎉",
            "author": "@excited_user",
            "engagement_metrics": {
                "likes": 300,
                "shares": 60,
                "comments": 20,
                "views": 12000,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "platform": "threads",
        }

        # Act
        response = client.post("/extract-patterns", json=special_post)

        # Assert
        assert response.status_code == 200
        patterns = response.json()

        # Should handle special characters and emojis
        assert "emotion_trajectory" in patterns
        trajectory = patterns["emotion_trajectory"]

        # Should detect roller coaster pattern from the varied emotional expressions
        assert trajectory["arc_type"] in [
            "roller_coaster",
            "rising",
            "falling",
            "steady",
        ]
        assert trajectory["emotional_variance"] > 0.2  # Should show some variance

    def test_api_rate_limiting_behavior(self, client, sample_viral_post):
        """Test API behavior under rapid successive requests."""
        post_data = sample_viral_post.dict()
        response_times = []

        # Make rapid successive requests
        for i in range(10):
            start_time = time.time()
            response = client.post("/extract-patterns", json=post_data)
            end_time = time.time()

            response_times.append((end_time - start_time) * 1000)
            assert response.status_code == 200

        # Response times should remain consistent (no degradation)
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 350
        assert max_response_time < 500, (
            f"Max response time {max_response_time:.2f}ms too high"
        )

        # Variance in response times should be reasonable
        variance = sum((rt - avg_response_time) ** 2 for rt in response_times) / len(
            response_times
        )
        std_dev = variance**0.5
        assert std_dev < 100, f"Response time variance too high: {std_dev:.2f}ms"
