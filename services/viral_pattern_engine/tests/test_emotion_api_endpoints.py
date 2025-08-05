"""API endpoint tests for emotion trajectory analysis."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from services.viral_pattern_engine.main import app


class TestEmotionAPIEndpoints:
    """Test FastAPI endpoints for emotion trajectory analysis."""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def sample_viral_post(self):
        """Create sample viral post data."""
        return {
            "id": "api_test_123",
            "author": "test_author",
            "content": "This is absolutely incredible! 🤯 I never thought I'd see such amazing results. At first I was skeptical, but now I'm completely convinced. This changes everything! You won't believe what happened next. Trust me, this is game-changing.",
            "created_at": "2025-01-01T00:00:00Z",
            "engagement_rate": 0.15,
            "likes": 2000,
            "comments": 120,
            "shares": 85,
            "views": 15000,
        }

    def test_extract_patterns_with_emotions(self, client, sample_viral_post):
        """Test /extract-patterns endpoint returns emotion analysis."""
        response = client.post("/extract-patterns", json=sample_viral_post)

        assert response.status_code == 200
        data = response.json()

        # Verify basic pattern extraction
        assert "hook_patterns" in data
        assert "emotion_patterns" in data
        assert "structure_patterns" in data
        assert "engagement_score" in data
        assert "pattern_strength" in data

        # Verify emotion patterns
        emotion_patterns = data["emotion_patterns"]
        assert len(emotion_patterns) > 0
        assert any(p["type"] == "excitement" for p in emotion_patterns)

        # Verify emotion trajectory for long content
        assert "emotion_trajectory" in data
        trajectory = data["emotion_trajectory"]

        if trajectory:  # Should have trajectory for this content length
            assert "trajectory_type" in trajectory
            assert "segments" in trajectory
            assert "dominant_emotion" in trajectory
            assert "emotional_variance" in trajectory
            assert "transitions" in trajectory

    def test_analyze_batch_with_emotions(self, client):
        """Test /analyze-batch endpoint with emotion analysis."""
        batch_request = {
            "posts": [
                {
                    "id": "batch_1",
                    "author": "author1",
                    "content": "Started feeling sad 😢 but then amazing things happened! 🎉 Now I'm ecstatic!",
                    "created_at": "2025-01-01T00:00:00Z",
                    "engagement_rate": 0.12,
                    "likes": 1500,
                    "comments": 80,
                    "shares": 50,
                    "views": 12000,
                },
                {
                    "id": "batch_2",
                    "author": "author2",
                    "content": "Consistently delivering great value. Quality content every time. Reliable results.",
                    "created_at": "2025-01-01T00:00:00Z",
                    "engagement_rate": 0.08,
                    "likes": 800,
                    "comments": 40,
                    "shares": 25,
                    "views": 8000,
                },
            ]
        }

        response = client.post("/analyze-batch", json=batch_request)

        assert response.status_code == 200
        data = response.json()

        # Verify batch response structure
        assert "results" in data
        assert "summary" in data
        assert len(data["results"]) == 2

        # Check first post (emotional)
        first_result = data["results"][0]
        assert "emotion_patterns" in first_result
        assert "emotion_trajectory" in first_result

        # Check summary includes emotion data
        summary = data["summary"]
        assert "total_emotion_patterns" in summary
        assert summary["total_emotion_patterns"] > 0

    def test_pattern_types_includes_emotions(self, client):
        """Test /pattern-types endpoint includes emotion categories."""
        response = client.get("/pattern-types")

        assert response.status_code == 200
        data = response.json()

        assert "emotion_patterns" in data
        emotion_types = data["emotion_patterns"]

        # Should include more emotion types now
        assert "excitement" in emotion_types
        assert "amazement" in emotion_types
        assert "surprise" in emotion_types

        # Could be extended to include all 8 emotions
        # assert "joy" in emotion_types
        # assert "sadness" in emotion_types
        # etc.

    def test_emotion_analysis_performance_endpoint(self, client):
        """Test that emotion analysis meets performance requirements via API."""
        import time

        # Create a longer post to trigger trajectory analysis
        long_post = {
            "id": "perf_test",
            "author": "test",
            "content": " ".join(
                [
                    "This is segment one with some emotion.",
                    "Segment two brings more excitement!",
                    "Third segment is absolutely amazing!",
                    "Fourth segment continues the journey.",
                    "Final segment concludes with triumph!",
                ]
                * 3
            ),  # Repeat to ensure sufficient length
            "created_at": "2025-01-01T00:00:00Z",
            "engagement_rate": 0.1,
            "likes": 1000,
            "comments": 50,
            "shares": 30,
            "views": 10000,
        }

        start_time = time.time()
        response = client.post("/extract-patterns", json=long_post)
        processing_time = (time.time() - start_time) * 1000  # ms

        assert response.status_code == 200
        assert processing_time < 500  # API overhead + processing should be under 500ms

        data = response.json()
        assert "emotion_trajectory" in data
        assert data["emotion_trajectory"] is not None

    def test_empty_content_handling(self, client):
        """Test API handles empty content gracefully."""
        empty_post = {
            "id": "empty_test",
            "author": "test",
            "content": "",
            "created_at": "2025-01-01T00:00:00Z",
            "engagement_rate": 0.0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
        }

        response = client.post("/extract-patterns", json=empty_post)

        assert response.status_code == 200
        data = response.json()

        # Should return empty patterns without crashing
        assert data["emotion_patterns"] == []
        assert data["hook_patterns"] == []
        assert "emotion_trajectory" not in data or data["emotion_trajectory"] is None

    def test_malformed_request_handling(self, client):
        """Test API handles malformed requests properly."""
        # Missing required fields
        malformed_post = {
            "id": "malformed_test",
            "content": "Some content",
            # Missing other required fields
        }

        response = client.post("/extract-patterns", json=malformed_post)

        # Should return 422 for validation error
        assert response.status_code == 422

    def test_concurrent_emotion_requests(self, client):
        """Test API handles concurrent emotion analysis requests."""
        import concurrent.futures

        posts = [
            {
                "id": f"concurrent_{i}",
                "author": "test",
                "content": f"Post {i}: Amazing discovery! This is incredible! Mind-blowing results!",
                "created_at": "2025-01-01T00:00:00Z",
                "engagement_rate": 0.1,
                "likes": 1000 * i,
                "comments": 50 * i,
                "shares": 30 * i,
                "views": 10000 * i,
            }
            for i in range(5)
        ]

        def make_request(post):
            return client.post("/extract-patterns", json=post)

        # Send concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, post) for post in posts]
            responses = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # Verify all requests succeeded
        assert len(responses) == 5
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "emotion_patterns" in data

    @patch(
        "services.viral_pattern_engine.emotion_analyzer.EmotionAnalyzer._load_bert_model"
    )
    @patch(
        "services.viral_pattern_engine.emotion_analyzer.EmotionAnalyzer._load_vader_analyzer"
    )
    def test_model_fallback_handling(self, mock_vader, mock_bert, client):
        """Test API handles model loading failures gracefully."""
        # Simulate model loading failure
        mock_bert.side_effect = Exception("Model loading failed")
        mock_vader.side_effect = Exception("VADER loading failed")

        post = {
            "id": "fallback_test",
            "author": "test",
            "content": "This is amazing! Incredible discovery!",
            "created_at": "2025-01-01T00:00:00Z",
            "engagement_rate": 0.1,
            "likes": 1000,
            "comments": 50,
            "shares": 30,
            "views": 10000,
        }

        response = client.post("/extract-patterns", json=post)

        # Should still work with fallback keyword analysis
        assert response.status_code == 200
        data = response.json()
        assert "emotion_patterns" in data
        assert len(data["emotion_patterns"]) > 0  # Should detect "amazing" via keywords

    def test_emotion_trajectory_metadata(self, client, sample_viral_post):
        """Test that emotion trajectory includes all required metadata."""
        response = client.post("/extract-patterns", json=sample_viral_post)

        assert response.status_code == 200
        data = response.json()

        trajectory = data.get("emotion_trajectory")
        if trajectory:
            # Verify all required fields
            assert "trajectory_type" in trajectory
            assert trajectory["trajectory_type"] in [
                "rising",
                "falling",
                "roller-coaster",
                "steady",
            ]

            assert "segments" in trajectory
            assert isinstance(trajectory["segments"], list)

            assert "dominant_emotion" in trajectory
            assert isinstance(trajectory["dominant_emotion"], str)

            assert "emotional_variance" in trajectory
            assert isinstance(trajectory["emotional_variance"], float)
            assert 0.0 <= trajectory["emotional_variance"] <= 1.0

            assert "peak_valley_count" in trajectory
            assert "peaks" in trajectory["peak_valley_count"]
            assert "valleys" in trajectory["peak_valley_count"]

            assert "transitions" in trajectory
            assert isinstance(trajectory["transitions"], list)

            # Check segment structure
            if trajectory["segments"]:
                segment = trajectory["segments"][0]
                assert "text" in segment
                assert "emotions" in segment
                assert "dominant_emotion" in segment
                assert "confidence" in segment
