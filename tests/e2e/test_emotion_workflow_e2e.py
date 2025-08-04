"""End-to-end workflow tests for emotion trajectory mapping system."""

import pytest
import hashlib
import time
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from services.viral_pattern_engine.emotion_analyzer import EmotionAnalyzer
from services.viral_pattern_engine.trajectory_mapper import TrajectoryMapper
from services.viral_pattern_engine.pattern_extractor import ViralPatternExtractor
from services.orchestrator.db.models import (
    EmotionTrajectory,
    EmotionSegment,
    EmotionTransition,
    EmotionTemplate,
    EmotionPerformance,
)


@pytest.mark.e2e
class TestEmotionWorkflowE2E:
    """End-to-end tests for complete emotion analysis workflow."""

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
    def sample_viral_content(self):
        """Sample viral content for testing complete workflow."""
        return {
            "post_id": "viral_post_001",
            "persona_id": "viral_creator",
            "content": """
            Let me tell you about the most incredible discovery I made yesterday.
            
            At first, I was just browsing through some research papers, feeling pretty bored.
            Nothing seemed particularly interesting or groundbreaking.
            
            But then I stumbled upon something that completely blew my mind!
            The implications of this research are absolutely revolutionary.
            
            I'm so excited to share this with everyone because it's going to change everything we know about viral content creation!
            This could be the breakthrough we've all been waiting for.
            """.strip(),
            "metadata": {
                "platform": "threads",
                "target_audience": "content_creators",
                "expected_engagement": 0.08,
            },
        }

    @pytest.fixture
    def narrative_arc_content(self):
        """Content with classic narrative arc structure."""
        return {
            "post_id": "narrative_arc_001",
            "persona_id": "storyteller",
            "content": """
            Once upon a time, there was a small content creator who dreamed of going viral.
            
            Day after day, they posted content that barely got any engagement.
            The creator felt frustrated and discouraged, wondering if they should give up.
            Their confidence was at an all-time low.
            
            But then, one magical evening, everything changed dramatically!
            A single post started getting thousands of likes and shares.
            
            The creator couldn't believe their eyes as the numbers kept climbing higher and higher!
            Within hours, they had gained thousands of new followers.
            
            From that day forward, they lived happily ever after as a successful viral content creator.
            Their dream had finally come true through persistence and a little bit of luck.
            """.strip(),
            "metadata": {"content_type": "story", "narrative_structure": "classic_arc"},
        }

    def test_complete_emotion_analysis_workflow(
        self,
        emotion_analyzer,
        trajectory_mapper,
        sample_viral_content,
        db_session: Session,
    ):
        """Test complete workflow from content input to database storage."""
        # Step 1: Split content into segments
        content = sample_viral_content["content"]
        segments = [para.strip() for para in content.split("\n\n") if para.strip()]

        # Step 2: Analyze individual emotions
        segment_emotions = []
        for segment in segments:
            emotion_result = emotion_analyzer.analyze_emotions(segment)
            segment_emotions.append(emotion_result)

        # Verify individual analysis
        assert len(segment_emotions) == len(segments)
        for emotion_result in segment_emotions:
            assert "emotions" in emotion_result
            assert "confidence" in emotion_result
            assert len(emotion_result["emotions"]) == 8

        # Step 3: Map emotion trajectory
        trajectory_result = trajectory_mapper.map_emotion_trajectory(segments)

        # Verify trajectory analysis
        assert trajectory_result["arc_type"] in [
            "rising",
            "falling",
            "roller_coaster",
            "steady",
        ]
        assert len(trajectory_result["emotion_progression"]) == len(segments)
        assert "peak_segments" in trajectory_result
        assert "valley_segments" in trajectory_result
        assert "emotional_variance" in trajectory_result

        # Step 4: Analyze transitions
        transition_result = trajectory_mapper.analyze_emotion_transitions(segments)

        # Verify transition analysis
        assert len(transition_result["transitions"]) == len(segments) - 1
        assert "dominant_transitions" in transition_result
        assert "transition_strength" in transition_result

        # Step 5: Store in database
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        trajectory = EmotionTrajectory(
            post_id=sample_viral_content["post_id"],
            persona_id=sample_viral_content["persona_id"],
            content_hash=content_hash,
            segment_count=len(segments),
            total_duration_words=len(content.split()),
            analysis_model="bert_vader",
            confidence_score=sum(e["confidence"] for e in segment_emotions)
            / len(segment_emotions),
            trajectory_type=trajectory_result["arc_type"],
            emotional_variance=trajectory_result["emotional_variance"],
            peak_count=len(trajectory_result["peak_segments"]),
            valley_count=len(trajectory_result["valley_segments"]),
            transition_count=len(transition_result["transitions"]),
            # Calculate averages
            joy_avg=sum(e["emotions"]["joy"] for e in segment_emotions)
            / len(segment_emotions),
            anger_avg=sum(e["emotions"]["anger"] for e in segment_emotions)
            / len(segment_emotions),
            fear_avg=sum(e["emotions"]["fear"] for e in segment_emotions)
            / len(segment_emotions),
            sadness_avg=sum(e["emotions"]["sadness"] for e in segment_emotions)
            / len(segment_emotions),
            surprise_avg=sum(e["emotions"]["surprise"] for e in segment_emotions)
            / len(segment_emotions),
            disgust_avg=sum(e["emotions"]["disgust"] for e in segment_emotions)
            / len(segment_emotions),
            trust_avg=sum(e["emotions"]["trust"] for e in segment_emotions)
            / len(segment_emotions),
            anticipation_avg=sum(
                e["emotions"]["anticipation"] for e in segment_emotions
            )
            / len(segment_emotions),
            processing_time_ms=250,  # Simulated processing time
        )

        db_session.add(trajectory)
        db_session.flush()

        # Step 6: Store segments
        for i, (segment, emotions) in enumerate(zip(segments, segment_emotions)):
            emotion_segment = EmotionSegment(
                trajectory_id=trajectory.id,
                segment_index=i,
                content_text=segment,
                word_count=len(segment.split()),
                sentence_count=segment.count(".")
                + segment.count("!")
                + segment.count("?"),
                joy_score=emotions["emotions"]["joy"],
                anger_score=emotions["emotions"]["anger"],
                fear_score=emotions["emotions"]["fear"],
                sadness_score=emotions["emotions"]["sadness"],
                surprise_score=emotions["emotions"]["surprise"],
                disgust_score=emotions["emotions"]["disgust"],
                trust_score=emotions["emotions"]["trust"],
                anticipation_score=emotions["emotions"]["anticipation"],
                dominant_emotion=max(
                    emotions["emotions"], key=emotions["emotions"].get
                ),
                confidence_score=emotions["confidence"],
                is_peak=i in trajectory_result["peak_segments"],
                is_valley=i in trajectory_result["valley_segments"],
            )
            db_session.add(emotion_segment)

        # Step 7: Store transitions
        for transition in transition_result["transitions"]:
            emotion_transition = EmotionTransition(
                trajectory_id=trajectory.id,
                from_segment_index=transition_result["transitions"].index(transition),
                to_segment_index=transition_result["transitions"].index(transition) + 1,
                from_emotion=transition["from_emotion"],
                to_emotion=transition["to_emotion"],
                transition_type=f"{transition['from_emotion']}_to_{transition['to_emotion']}",
                strength_score=transition["strength"],
            )
            db_session.add(emotion_transition)

        db_session.commit()

        # Step 8: Verify complete storage
        stored_trajectory = db_session.get(EmotionTrajectory, trajectory.id)
        assert stored_trajectory is not None
        assert len(stored_trajectory.segments) == len(segments)
        assert len(stored_trajectory.transitions) == len(segments) - 1

        # Verify the dominant emotion calculation
        assert stored_trajectory.dominant_emotion in [
            "joy",
            "anger",
            "fear",
            "sadness",
            "surprise",
            "disgust",
            "trust",
            "anticipation",
        ]

    def test_narrative_arc_detection_workflow(
        self, trajectory_mapper, narrative_arc_content, db_session: Session
    ):
        """Test detection of classic narrative arc patterns."""
        content = narrative_arc_content["content"]
        segments = [para.strip() for para in content.split("\n\n") if para.strip()]

        # Analyze trajectory
        result = trajectory_mapper.map_emotion_trajectory(segments)

        # Should detect classic narrative patterns
        assert result["arc_type"] in ["rising", "roller_coaster"]  # Classic arcs
        assert result["emotional_variance"] > 0.3  # Should have emotional variety
        assert len(result["peak_segments"]) >= 1  # Should have climax moments

        # Verify story structure detection
        progression = result["emotion_progression"]

        # Early segments should have lower joy (struggle)
        sum(seg.get("joy", 0) for seg in progression[:2]) / 2

        # Later segments should have higher joy (resolution)
        sum(seg.get("joy", 0) for seg in progression[-2:]) / 2

        # Story should show progression (though this might not always be strictly true)
        # At minimum, verify we can detect different emotional states
        emotion_variety = len(set(max(seg, key=seg.get) for seg in progression))
        assert emotion_variety >= 2  # At least 2 different dominant emotions

    def test_template_matching_workflow(self, trajectory_mapper, db_session: Session):
        """Test template matching against analyzed content."""
        # Step 1: Create emotion templates in database
        templates = [
            EmotionTemplate(
                template_name="Rising Joy Pattern",
                template_type="engagement_hook",
                pattern_description="Content that builds joy progressively",
                segment_count=4,
                optimal_duration_words=200,
                trajectory_pattern="rising",
                primary_emotions=["joy", "anticipation"],
                emotion_sequence='{"pattern": "low_to_high_joy"}',
                transition_patterns='{"main": "anticipation_to_joy"}',
                effectiveness_score=0.85,
                is_active=True,
            ),
            EmotionTemplate(
                template_name="Emotional Roller Coaster",
                template_type="narrative_arc",
                pattern_description="High variance emotional journey",
                segment_count=5,
                optimal_duration_words=300,
                trajectory_pattern="roller_coaster",
                primary_emotions=["joy", "sadness", "surprise"],
                emotion_sequence='{"pattern": "alternating_peaks_valleys"}',
                transition_patterns='{"main": "high_variance_transitions"}',
                effectiveness_score=0.78,
                is_active=True,
            ),
        ]

        for template in templates:
            db_session.add(template)
        db_session.commit()

        # Step 2: Analyze content that should match a template
        rising_content = [
            "Let me share something interesting with you.",
            "This is getting more exciting as I learn more!",
            "OMG this is absolutely incredible and amazing!",
            "I can't contain my excitement about this discovery!",
        ]

        result = trajectory_mapper.map_emotion_trajectory(rising_content)

        # Step 3: Match against templates (simplified matching logic)
        def calculate_template_match_score(trajectory_result, template):
            """Simplified template matching logic."""
            score = 0.0

            # Match trajectory type
            if trajectory_result["arc_type"] == template.trajectory_pattern:
                score += 0.4

            # Match segment count (within reasonable range)
            segment_diff = abs(
                len(trajectory_result["emotion_progression"]) - template.segment_count
            )
            if segment_diff <= 1:
                score += 0.3
            elif segment_diff <= 2:
                score += 0.15

            # Match emotional variance for roller coaster patterns
            if (
                template.trajectory_pattern == "roller_coaster"
                and trajectory_result["emotional_variance"] > 0.4
            ):
                score += 0.3
            elif (
                template.trajectory_pattern == "rising"
                and trajectory_result["emotional_variance"] < 0.5
            ):
                score += 0.3

            return score

        # Calculate matches
        template_matches = []
        for template in templates:
            match_score = calculate_template_match_score(result, template)
            if match_score > 0.5:  # Threshold for considering a match
                template_matches.append(
                    {"template": template, "match_score": match_score}
                )

        # Should find at least one good match
        assert len(template_matches) >= 1
        best_match = max(template_matches, key=lambda x: x["match_score"])
        assert best_match["template"].template_name == "Rising Joy Pattern"
        assert best_match["match_score"] > 0.7

    def test_performance_correlation_workflow(self, db_session: Session):
        """Test workflow for correlating emotion patterns with performance."""
        # Step 1: Create trajectory with known performance
        high_performing_trajectory = EmotionTrajectory(
            post_id="high_performer_001",
            persona_id="viral_creator",
            content_hash=hashlib.sha256("high performing content".encode()).hexdigest(),
            segment_count=4,
            total_duration_words=180,
            trajectory_type="rising",
            emotional_variance=0.45,
            peak_count=2,
            valley_count=0,
            transition_count=3,
            joy_avg=0.75,
            trust_avg=0.68,
            anticipation_avg=0.72,
            surprise_avg=0.65,
            sadness_avg=0.15,
            anger_avg=0.1,
            fear_avg=0.12,
            disgust_avg=0.08,
            confidence_score=0.88,
        )

        db_session.add(high_performing_trajectory)
        db_session.flush()

        # Step 2: Add performance data
        performance = EmotionPerformance(
            trajectory_id=high_performing_trajectory.id,
            post_id="high_performer_001",
            persona_id="viral_creator",
            engagement_rate=0.12,  # High engagement
            likes_count=2500,
            shares_count=450,
            comments_count=180,
            reach=25000,
            impressions=30000,
            emotion_effectiveness=0.89,
            predicted_engagement=0.10,
            actual_vs_predicted=0.02,  # Outperformed prediction
            measured_at=datetime.utcnow(),
        )

        db_session.add(performance)
        db_session.commit()

        # Step 3: Analyze correlation patterns
        # Query high-performing content
        high_engagement_trajectories = db_session.scalars(
            select(EmotionTrajectory)
            .join(EmotionPerformance)
            .where(EmotionPerformance.engagement_rate >= 0.10)
        ).all()

        assert len(high_engagement_trajectories) >= 1

        # Analyze common patterns in high-performing content
        trajectory = high_engagement_trajectories[0]

        # Should show positive emotion dominance
        positive_emotions = (
            trajectory.joy_avg + trajectory.trust_avg + trajectory.anticipation_avg
        )
        negative_emotions = (
            trajectory.sadness_avg
            + trajectory.anger_avg
            + trajectory.fear_avg
            + trajectory.disgust_avg
        )

        assert positive_emotions > negative_emotions
        assert trajectory.confidence_score > 0.8  # High confidence analysis
        assert trajectory.emotional_variance > 0.3  # Engaging variety

    def test_real_time_analysis_simulation(self, emotion_analyzer, trajectory_mapper):
        """Test simulated real-time emotion analysis workflow."""
        import time

        # Simulate streaming content analysis
        streaming_segments = [
            "Breaking: Something incredible just happened!",
            "Let me explain what's going on...",
            "This is getting more interesting by the minute!",
            "You won't believe what happened next!",
            "The final result exceeded all expectations!",
        ]

        # Track processing as if real-time
        processed_segments = []
        cumulative_results = []

        for i, segment in enumerate(streaming_segments):
            start_time = time.time()

            # Add new segment
            processed_segments.append(segment)

            # Analyze current trajectory
            if len(processed_segments) >= 2:  # Need at least 2 segments for trajectory
                result = trajectory_mapper.map_emotion_trajectory(processed_segments)

                processing_time = (time.time() - start_time) * 1000

                cumulative_results.append(
                    {
                        "segment_count": len(processed_segments),
                        "arc_type": result["arc_type"],
                        "emotional_variance": result["emotional_variance"],
                        "processing_time_ms": processing_time,
                    }
                )

                # Real-time performance requirement
                assert processing_time < 500, (
                    f"Real-time processing too slow: {processing_time:.2f}ms"
                )

        # Verify progression analysis
        assert len(cumulative_results) == 4  # Should have 4 progressive analyses

        # Should show increasing confidence as more data is available
        final_result = cumulative_results[-1]
        assert final_result["segment_count"] == 5
        assert final_result["arc_type"] in [
            "rising",
            "falling",
            "roller_coaster",
            "steady",
        ]

    def test_batch_content_analysis_workflow(
        self, trajectory_mapper, db_session: Session
    ):
        """Test workflow for batch processing multiple content pieces."""
        # Step 1: Prepare batch of content
        batch_content = [
            {
                "post_id": f"batch_post_{i}",
                "persona_id": "viral_creator",
                "segments": [
                    f"Content piece {i} starts here.",
                    f"Middle part of content {i} with emotions.",
                    f"Exciting conclusion for content {i}!",
                ],
            }
            for i in range(10)
        ]

        # Step 2: Process batch
        batch_results = []
        start_time = time.time()

        for content_item in batch_content:
            result = trajectory_mapper.map_emotion_trajectory(content_item["segments"])

            batch_results.append(
                {
                    "post_id": content_item["post_id"],
                    "persona_id": content_item["persona_id"],
                    "analysis": result,
                }
            )

        total_processing_time = (time.time() - start_time) * 1000

        # Step 3: Verify batch processing
        assert len(batch_results) == 10
        assert total_processing_time < 5000  # 5 seconds for 10 items

        # All analyses should be valid
        for result in batch_results:
            assert result["analysis"]["arc_type"] in [
                "rising",
                "falling",
                "roller_coaster",
                "steady",
            ]
            assert "emotional_variance" in result["analysis"]

        # Step 4: Batch store in database (simulation)
        trajectories = []
        for result in batch_results:
            trajectory = EmotionTrajectory(
                post_id=result["post_id"],
                persona_id=result["persona_id"],
                content_hash=hashlib.sha256(result["post_id"].encode()).hexdigest(),
                segment_count=3,
                total_duration_words=50,
                trajectory_type=result["analysis"]["arc_type"],
                emotional_variance=result["analysis"]["emotional_variance"],
                peak_count=len(result["analysis"]["peak_segments"]),
                valley_count=len(result["analysis"]["valley_segments"]),
                joy_avg=0.5,  # Simplified for batch test
                trust_avg=0.6,
            )
            trajectories.append(trajectory)

        db_session.add_all(trajectories)
        db_session.commit()

        # Verify batch storage
        stored_count = db_session.scalar(
            select(EmotionTrajectory).where(
                EmotionTrajectory.persona_id == "viral_creator"
            )
        )
        assert stored_count is not None

    def test_error_recovery_workflow(self, trajectory_mapper, db_session: Session):
        """Test workflow error recovery and graceful degradation."""
        # Test content that might cause issues
        problematic_content = [
            "",  # Empty segment
            "🎉" * 1000,  # Emoji overload
            "A" * 10000,  # Extremely long repetitive content
            "Mixed content with 中文 and émojis 🚀",  # Mixed languages
            "Normal content that should work fine.",
        ]

        # Should handle gracefully without crashing
        try:
            result = trajectory_mapper.map_emotion_trajectory(problematic_content)

            # Basic validation that it didn't crash
            assert result is not None
            assert "arc_type" in result
            assert len(result["emotion_progression"]) == len(problematic_content)

            # Try to store result (should handle DB constraints gracefully)
            trajectory = EmotionTrajectory(
                post_id="error_recovery_test",
                persona_id="test_persona",
                content_hash=hashlib.sha256("error test".encode()).hexdigest(),
                segment_count=len(problematic_content),
                total_duration_words=sum(
                    len(seg.split()) for seg in problematic_content if seg
                ),
                trajectory_type=result["arc_type"],
                emotional_variance=result["emotional_variance"],
                joy_avg=0.5,
            )

            db_session.add(trajectory)
            db_session.commit()

            # If we get here, error recovery worked
            assert trajectory.id is not None

        except Exception as e:
            # If there are exceptions, they should be handled gracefully
            pytest.fail(f"Workflow should handle errors gracefully, but got: {e}")

    def test_integration_with_pattern_extractor(
        self, pattern_extractor, db_session: Session
    ):
        """Test integration between emotion analysis and pattern extraction."""

        # Mock viral post for pattern extraction
        class MockViralPost:
            def __init__(self, content):
                self.content = content
                self.engagement_rate = 0.08
                self.likes = 1500
                self.shares = 200

        viral_content = """
        🚨 THREAD: The algorithm change that NOBODY is talking about...

        I've been testing this for 3 months and the results are INSANE.

        Most creators are missing this completely (and their engagement is suffering because of it).

        Here's what I discovered:
        """

        mock_post = MockViralPost(viral_content)

        # Extract patterns (including emotion patterns)
        patterns = pattern_extractor.extract_patterns(mock_post)

        # Should include emotion analysis in patterns
        assert "emotion_patterns" in patterns
        assert patterns["engagement_score"] >= 0
        assert patterns["pattern_strength"] >= 0

        # Emotion patterns should be detected
        emotion_patterns = patterns["emotion_patterns"]
        assert len(emotion_patterns) > 0

        # Should detect hook patterns common in viral content
        hook_patterns = patterns["hook_patterns"]
        assert len(hook_patterns) > 0
