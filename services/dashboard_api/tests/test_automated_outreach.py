"""
Test suite for automated follow-up and outreach system.

This module tests the automated outreach functionality that converts
content engagement into job opportunity conversations.

Following TDD principles - writing failing tests first.
"""

from datetime import datetime, timedelta

from lead_scoring import LeadScoringEngine, VisitorBehavior, LeadScore


class TestHighEngagementUserDetection:
    """Test high-engagement user detection for automated outreach"""

    def test_detect_high_engagement_users_returns_qualified_leads(self):
        """
        Test that high-engagement user detection identifies users
        with hiring_manager_probability > 0.7 for outreach.

        This test will fail because OutreachEngine doesn't exist yet.
        """
        # Arrange - This will fail because OutreachEngine doesn't exist
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()
        lead_engine = LeadScoringEngine()

        # Create high-engagement behaviors for a hiring manager
        visitor_id = "visitor_hm_001"
        behaviors = [
            VisitorBehavior(
                visitor_id=visitor_id,
                page_url="https://serbyn.pro/portfolio",
                time_on_page_seconds=240,  # 4 minutes
                scroll_depth_percent=95,
                utm_source="linkedin",
            ),
            VisitorBehavior(
                visitor_id=visitor_id,
                page_url="https://serbyn.pro/contact",
                time_on_page_seconds=120,  # 2 minutes
                scroll_depth_percent=100,
                utm_source="linkedin",
            ),
        ]

        # Calculate lead score (should be high)
        lead_score = lead_engine.calculate_lead_score(visitor_id, behaviors)

        # Act - Detect high-engagement users
        qualified_leads = outreach_engine.detect_high_engagement_users([lead_score])

        # Assert
        assert len(qualified_leads) == 1
        assert qualified_leads[0]["visitor_id"] == visitor_id
        assert qualified_leads[0]["hiring_manager_probability"] > 0.7
        assert qualified_leads[0]["outreach_priority"] == "high"
        assert "linkedin" in qualified_leads[0]["traffic_sources"]

    def test_detect_high_engagement_filters_out_developers(self):
        """
        Test that developer-focused visitors are filtered out
        even with high engagement scores.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()
        lead_engine = LeadScoringEngine()

        # Create developer-focused behaviors
        visitor_id = "visitor_dev_001"
        behaviors = [
            VisitorBehavior(
                visitor_id=visitor_id,
                page_url="https://serbyn.pro/portfolio/mlops-technical",
                time_on_page_seconds=600,  # 10 minutes - very engaged
                scroll_depth_percent=100,
                utm_source="devto",  # Developer source
            )
        ]

        lead_score = lead_engine.calculate_lead_score(visitor_id, behaviors)

        # Act
        qualified_leads = outreach_engine.detect_high_engagement_users([lead_score])

        # Assert - Should be empty because it's a developer
        assert len(qualified_leads) == 0

    def test_detect_high_engagement_includes_company_context(self):
        """
        Test that company information is included for target company prioritization.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Mock visitor with Google email
        visitor_email = "hiring@google.com"
        lead_score = LeadScore(
            visitor_id="visitor_google_001",
            total_score=85,
            hiring_manager_probability=0.8,
            visitor_type="hiring_manager",
            score_breakdown={"linkedin_professional": 15, "contact_intent": 30},
            calculated_at=datetime.utcnow(),
        )

        # Act - Should include company context
        qualified_leads = outreach_engine.detect_high_engagement_users(
            [lead_score], visitor_emails={"visitor_google_001": visitor_email}
        )

        # Assert
        assert len(qualified_leads) == 1
        lead = qualified_leads[0]
        assert lead["company_name"] == "Google"
        assert lead["is_target_company"] is True
        assert (
            lead["outreach_priority"] == "urgent"
        )  # Target company gets urgent priority


class TestLinkedInOutreachAutomation:
    """Test LinkedIn outreach automation functionality"""

    def test_generate_linkedin_connection_request_with_personalization(self):
        """
        Test automated LinkedIn connection request generation with
        personalized messages based on engagement data.

        This test will fail because LinkedIn outreach functionality doesn't exist yet.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange - qualified lead from Google
        qualified_lead = {
            "visitor_id": "visitor_google_hm",
            "hiring_manager_probability": 0.85,
            "outreach_priority": "urgent",
            "traffic_sources": ["linkedin"],
            "company_name": "Google",
            "is_target_company": True,
            "engagement_pages": [
                "https://serbyn.pro/portfolio/mlops-projects",
                "https://serbyn.pro/contact",
            ],
            "time_on_site": 480,  # 8 minutes
        }

        # Act - Generate LinkedIn connection request
        connection_request = outreach_engine.generate_linkedin_connection_request(
            qualified_lead
        )

        # Assert
        assert connection_request["platform"] == "linkedin"
        assert connection_request["message_type"] == "connection_request"
        assert len(connection_request["message"]) <= 200  # LinkedIn limit
        assert "Google" in connection_request["message"]  # Company mentioned
        assert "MLOps" in connection_request["message"]  # Technical focus mentioned
        assert connection_request["personalization_score"] >= 0.7
        assert connection_request["send_priority"] == "urgent"

    def test_generate_linkedin_follow_up_message_sequence(self):
        """
        Test LinkedIn follow-up message generation after connection acceptance.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange
        qualified_lead = {
            "visitor_id": "visitor_meta_hm",
            "company_name": "Meta",
            "engagement_pages": ["https://serbyn.pro/portfolio"],
            "hiring_manager_probability": 0.75,
        }

        connection_status = {
            "connection_accepted": True,
            "accepted_at": datetime.utcnow(),
            "connection_response": None,  # No reply yet
        }

        # Act
        follow_up_sequence = outreach_engine.generate_linkedin_follow_up_sequence(
            qualified_lead, connection_status
        )

        # Assert
        assert len(follow_up_sequence) >= 2  # At least 2 follow-up messages

        # First follow-up (immediate after connection)
        first_message = follow_up_sequence[0]
        assert first_message["delay_hours"] == 0  # Immediate
        assert first_message["message_type"] == "initial_follow_up"
        assert "thank" in first_message["message"].lower()

        # Second follow-up (if no response)
        second_message = follow_up_sequence[1]
        assert second_message["delay_hours"] == 72  # 3 days
        assert second_message["message_type"] == "value_proposition"
        assert len(second_message["message"]) <= 500  # LinkedIn message limit

    def test_track_linkedin_outreach_responses(self):
        """
        Test tracking and categorizing responses from LinkedIn outreach.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange
        outreach_record = {
            "outreach_id": "linkedin_001",
            "visitor_id": "visitor_stripe_hm",
            "platform": "linkedin",
            "message_sent": True,
            "sent_at": datetime.utcnow() - timedelta(hours=24),
        }

        # Mock LinkedIn response
        linkedin_response = {
            "message": "Hi! Thanks for connecting. I'm actually looking for MLOps engineers for our team. Would love to chat about opportunities.",
            "received_at": datetime.utcnow(),
            "sender_profile": "linkedin.com/in/stripe-hiring-manager",
        }

        # Act
        response_analysis = outreach_engine.track_linkedin_response(
            outreach_record, linkedin_response
        )

        # Assert
        assert response_analysis["response_received"] is True
        assert (
            response_analysis["response_type"] == "job_opportunity"
        )  # AI categorization
        assert response_analysis["hiring_intent_score"] >= 0.8  # High hiring intent
        assert response_analysis["next_action"] == "schedule_call"
        assert "mlops" in response_analysis["mentioned_keywords"]
        assert response_analysis["response_sentiment"] == "positive"


class TestEmailFollowUpAutomation:
    """Test email follow-up sequence automation functionality"""

    def test_generate_email_follow_up_sequence_for_contact_form_submission(self):
        """
        Test automated email follow-up sequence generation for contact form submissions.

        This test will fail because email automation functionality doesn't exist yet.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange - Contact form submission from qualified lead
        contact_submission = {
            "visitor_id": "visitor_amazon_hm",
            "email": "hiring-manager@amazon.com",
            "name": "Sarah Chen",
            "company": "Amazon",
            "message": "Hi! Interested in discussing MLOps opportunities for our AI team.",
            "submitted_at": datetime.utcnow(),
            "form_source": "contact_page",
        }

        lead_context = {
            "hiring_manager_probability": 0.9,
            "engagement_pages": [
                "https://serbyn.pro/portfolio/mlops-projects",
                "https://serbyn.pro/contact",
            ],
            "time_on_site": 420,  # 7 minutes
            "utm_source": "linkedin",
        }

        # Act - Generate email follow-up sequence
        email_sequence = outreach_engine.generate_email_follow_up_sequence(
            contact_submission, lead_context
        )

        # Assert
        assert len(email_sequence) >= 3  # At least 3 emails in sequence

        # First email (immediate thank you)
        first_email = email_sequence[0]
        assert first_email["delay_hours"] == 0
        assert first_email["email_type"] == "thank_you_response"
        assert first_email["subject"].startswith("Thank you")
        assert "Sarah" in first_email["body"]  # Personalized
        assert "Amazon" in first_email["body"]  # Company mentioned

        # Second email (follow-up with portfolio)
        second_email = email_sequence[1]
        assert second_email["delay_hours"] == 24  # 1 day later
        assert second_email["email_type"] == "portfolio_showcase"
        assert "MLOps" in second_email["body"]

        # Third email (call-to-action)
        third_email = email_sequence[2]
        assert third_email["delay_hours"] == 168  # 1 week later
        assert third_email["email_type"] == "call_to_action"
        assert "schedule" in third_email["body"].lower()

    def test_generate_email_sequence_for_high_engagement_no_contact(self):
        """
        Test email outreach for high-engagement visitors who didn't submit contact form.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange - High engagement but no contact form submission
        visitor_profile = {
            "visitor_id": "visitor_netflix_hm",
            "email": "tech-lead@netflix.com",  # Obtained through lead enrichment
            "company": "Netflix",
            "hiring_manager_probability": 0.8,
            "engagement_pages": [
                "https://serbyn.pro/portfolio",
                "https://serbyn.pro/portfolio/mlops-projects",
            ],
            "time_on_site": 600,  # 10 minutes
            "utm_source": "linkedin",
            "last_visit": datetime.utcnow() - timedelta(hours=48),  # 2 days ago
        }

        # Act
        proactive_email_sequence = outreach_engine.generate_proactive_email_sequence(
            visitor_profile
        )

        # Assert
        assert len(proactive_email_sequence) >= 2

        first_email = proactive_email_sequence[0]
        assert first_email["email_type"] == "gentle_outreach"
        assert first_email["subject"].startswith("Following up")
        assert "Netflix" in first_email["body"]
        assert first_email["tone"] == "professional_soft"

    def test_track_email_engagement_and_responses(self):
        """
        Test tracking email engagement (opens, clicks, replies) for follow-up optimization.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange
        email_campaign = {
            "email_id": "email_001_amazon",
            "visitor_id": "visitor_amazon_hm",
            "email_type": "thank_you_response",
            "sent_at": datetime.utcnow() - timedelta(hours=12),
            "recipient": "hiring-manager@amazon.com",
        }

        # Mock email engagement data
        engagement_data = {
            "opened": True,
            "opened_at": datetime.utcnow() - timedelta(hours=10),
            "clicked_links": ["https://serbyn.pro/portfolio/mlops-projects"],
            "reply_received": True,
            "reply_message": "Thanks for reaching out! I'd like to schedule a call to discuss opportunities on our ML Platform team.",
            "reply_received_at": datetime.utcnow() - timedelta(hours=2),
        }

        # Act
        engagement_analysis = outreach_engine.track_email_engagement(
            email_campaign, engagement_data
        )

        # Assert
        assert engagement_analysis["email_opened"] is True
        assert engagement_analysis["links_clicked"] == 1
        assert engagement_analysis["reply_received"] is True
        assert engagement_analysis["reply_type"] == "job_discussion"
        assert engagement_analysis["engagement_score"] >= 0.8  # High engagement
        assert engagement_analysis["next_action"] == "schedule_call"
        assert engagement_analysis["lead_quality"] == "hot"


class TestAIPersonalizedOutreachMessages:
    """Test AI-generated personalized outreach message creation"""

    def test_generate_ai_personalized_linkedin_message_with_achievements(self):
        """
        Test AI-generated LinkedIn message personalization using specific achievements.

        This test will fail because AI personalization functionality doesn't exist yet.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange - Lead with specific technical interests
        qualified_lead = {
            "visitor_id": "visitor_uber_ml_lead",
            "company_name": "Uber",
            "hiring_manager_probability": 0.85,
            "engagement_pages": [
                "https://serbyn.pro/portfolio/mlflow-registry-optimization",
                "https://serbyn.pro/portfolio/kubernetes-ml-deployment",
            ],
            "time_on_site": 540,  # 9 minutes
            "utm_source": "linkedin",
        }

        # Available achievements to draw from for personalization
        achievement_context = {
            "mlops_achievements": [
                {
                    "title": "MLflow Registry Multi-Algorithm Training System",
                    "impact": "Reduced ML training costs by 60% through automated algorithm comparison",
                    "technologies": ["MLflow", "Python", "Scikit-learn", "XGBoost"],
                    "metrics": {"cost_reduction": 60, "accuracy_improvement": 15},
                },
                {
                    "title": "Kubernetes ML Model Deployment Pipeline",
                    "impact": "Achieved 99.9% uptime for ML model serving with automated rollback",
                    "technologies": ["Kubernetes", "Docker", "Prometheus", "Grafana"],
                    "metrics": {"uptime": 99.9, "deployment_time_reduction": 80},
                },
            ],
            "visitor_technical_interests": ["mlflow", "kubernetes", "ml-deployment"],
        }

        # Act - Generate AI-personalized message
        ai_message = outreach_engine.generate_ai_personalized_message(
            qualified_lead, achievement_context, message_type="linkedin_connection"
        )

        # Assert
        assert ai_message["platform"] == "linkedin"
        assert ai_message["personalization_type"] == "ai_generated"
        assert ai_message["relevance_score"] >= 0.8  # High relevance

        # Should mention specific achievements based on their interests
        message_content = ai_message["message"].lower()
        assert "mlflow" in message_content or "kubernetes" in message_content
        assert (
            "60%" in ai_message["message"] or "99.9%" in ai_message["message"]
        )  # Specific metrics
        assert "uber" in message_content

        # Should include call-to-action
        assert any(
            word in message_content for word in ["discuss", "chat", "call", "connect"]
        )

        # Metadata for tracking effectiveness
        assert ai_message["achievements_referenced"] >= 1
        assert len(ai_message["technologies_mentioned"]) >= 2

    def test_generate_ai_personalized_email_with_company_context(self):
        """
        Test AI-generated email personalization based on company-specific challenges.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange
        contact_submission = {
            "visitor_id": "visitor_netflix_senior_engineer",
            "email": "ml-platform@netflix.com",
            "name": "Alex Rodriguez",
            "company": "Netflix",
            "message": "Interested in your experience with large-scale ML systems and cost optimization.",
        }

        # Company-specific context and achievements
        company_context = {
            "industry": "streaming_media",
            "known_challenges": [
                "large-scale ML",
                "content recommendation",
                "cost optimization",
            ],
            "company_size": "large",
            "ml_maturity": "advanced",
        }

        achievement_context = {
            "relevant_achievements": [
                {
                    "title": "Large-Scale ML Pipeline Cost Optimization",
                    "impact": "Reduced training costs by $50K/month through intelligent resource allocation",
                    "relevance_to_netflix": 0.9,
                },
                {
                    "title": "Real-time ML Model Serving at Scale",
                    "impact": "Handled 1M+ predictions/second with <100ms latency",
                    "relevance_to_netflix": 0.85,
                },
            ]
        }

        # Act
        ai_personalized_email = outreach_engine.generate_ai_personalized_email(
            contact_submission, company_context, achievement_context
        )

        # Assert
        assert ai_personalized_email["email_type"] == "ai_personalized_response"
        assert ai_personalized_email["company_relevance_score"] >= 0.8

        email_body = ai_personalized_email["body"].lower()
        assert "netflix" in email_body
        assert "alex" in email_body  # Personalized name
        assert (
            "streaming" in email_body or "recommendation" in email_body
        )  # Industry context
        assert (
            "$50k" in ai_personalized_email["body"] or "1m+" in email_body
        )  # Specific metrics

        # Should reference their specific interest in cost optimization
        assert "cost optimization" in email_body
        assert ai_personalized_email["achievements_highlighted"] >= 2

    def test_ai_message_optimization_based_on_engagement_patterns(self):
        """
        Test AI message optimization based on historical engagement patterns.
        """
        from automated_outreach import OutreachEngine

        outreach_engine = OutreachEngine()

        # Arrange - Historical engagement data for optimization
        engagement_patterns = {
            "successful_messages": [
                {
                    "message_type": "technical_focus",
                    "response_rate": 0.65,
                    "key_elements": ["specific metrics", "technical depth", "brief"],
                },
                {
                    "message_type": "business_impact",
                    "response_rate": 0.45,
                    "key_elements": ["cost savings", "roi", "case studies"],
                },
            ],
            "target_audience": "senior_ml_engineers",
            "optimal_length": "150-200 chars",
            "best_call_to_action": "brief technical call",
        }

        qualified_lead = {
            "visitor_id": "visitor_stripe_principal_engineer",
            "company_name": "Stripe",
            "visitor_seniority": "principal",
            "technical_focus": True,
        }

        # Act - Generate optimized message
        optimized_message = outreach_engine.generate_optimized_ai_message(
            qualified_lead,
            engagement_patterns,
            optimization_goal="maximize_response_rate",
        )

        # Assert
        assert optimized_message["optimization_score"] >= 0.6
        assert optimized_message["predicted_response_rate"] >= 0.5
        assert (
            optimized_message["message_type"] == "technical_focus"
        )  # Should pick highest performing
        assert 150 <= len(optimized_message["message"]) <= 200  # Optimal length
        assert "technical" in optimized_message["message"].lower()
        assert "call" in optimized_message["message"].lower()  # Best CTA included
