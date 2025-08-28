"""
Test-driven development for UTM tracking and lead scoring system.

This test file implements TDD for the third feature of the marketing automation epic:
"serbyn.pro Traffic Driver with UTM Tracking & Lead Scoring"

Test Coverage:
1. UTM Parameter Processing and Validation
2. Lead Scoring Engine based on visitor behavior
3. Conversion Funnel Tracking (Content → Visit → Lead)
4. A/B Testing Framework for conversion optimization
"""

import pytest
from datetime import datetime, timedelta

# This will fail initially - we're implementing TDD
import sys

sys.path.append(
    "/Users/vitaliiserbyn/development/wt-a3-analytics/services/dashboard_api"
)

from utm_tracker import UTMParameterProcessor, UTMValidationError
from lead_scoring import LeadScoringEngine, VisitorBehavior, LeadScore
from conversion_funnel import ConversionFunnelTracker, ConversionEvent
from ab_testing import ABTestingFramework, TestVariant


class TestUTMParameterProcessing:
    """Test UTM parameter extraction, validation, and storage"""

    def test_extract_utm_parameters_from_valid_url(self):
        """Test that UTM parameters are correctly extracted from URLs"""
        processor = UTMParameterProcessor()

        url = "https://serbyn.pro/portfolio?utm_source=linkedin&utm_medium=social&utm_campaign=pr_automation&utm_content=case_study&utm_term=mlops"

        result = processor.extract_utm_parameters(url)

        expected = {
            "utm_source": "linkedin",
            "utm_medium": "social",
            "utm_campaign": "pr_automation",
            "utm_content": "case_study",
            "utm_term": "mlops",
        }

        assert result == expected

    def test_extract_utm_parameters_partial_params(self):
        """Test extraction when only some UTM parameters are present"""
        processor = UTMParameterProcessor()

        url = "https://serbyn.pro/contact?utm_source=twitter&utm_campaign=job_search"

        result = processor.extract_utm_parameters(url)

        expected = {"utm_source": "twitter", "utm_campaign": "job_search"}

        assert result == expected

    def test_validate_utm_parameters_required_fields(self):
        """Test that validation enforces required UTM parameters"""
        processor = UTMParameterProcessor()

        # Should pass with required fields
        valid_params = {"utm_source": "linkedin", "utm_campaign": "pr_automation"}
        assert processor.validate_utm_parameters(valid_params) == True

        # Should fail without utm_source
        invalid_params = {"utm_campaign": "pr_automation"}
        with pytest.raises(UTMValidationError, match="utm_source is required"):
            processor.validate_utm_parameters(invalid_params)

        # Should fail without utm_campaign
        invalid_params = {"utm_source": "linkedin"}
        with pytest.raises(UTMValidationError, match="utm_campaign is required"):
            processor.validate_utm_parameters(invalid_params)

    def test_validate_utm_source_allowed_values(self):
        """Test that utm_source validation enforces allowed platforms"""
        processor = UTMParameterProcessor()

        # Should pass with allowed source
        valid_params = {"utm_source": "linkedin", "utm_campaign": "pr_automation"}
        assert processor.validate_utm_parameters(valid_params) == True

        # Should fail with disallowed source
        invalid_params = {
            "utm_source": "invalid_platform",
            "utm_campaign": "pr_automation",
        }
        with pytest.raises(UTMValidationError, match="Invalid utm_source"):
            processor.validate_utm_parameters(invalid_params)

    def test_store_utm_analytics_creates_tracking_record(self):
        """Test that UTM analytics are properly stored for analysis"""
        processor = UTMParameterProcessor()

        utm_params = {
            "utm_source": "devto",
            "utm_medium": "article",
            "utm_campaign": "pr_automation",
            "utm_content": "technical_case_study",
        }

        visitor_info = {
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "timestamp": "2025-01-15T10:30:00Z",
        }

        result = processor.store_utm_analytics(utm_params, visitor_info)

        assert result["success"] == True
        assert "tracking_id" in result
        assert result["platform"] == "devto"
        assert result["campaign"] == "pr_automation"


class TestLeadScoringEngine:
    """Test visitor behavior tracking and lead scoring"""

    def test_track_visitor_behavior_creates_behavior_record(self):
        """Test that visitor behaviors are tracked for lead scoring"""
        engine = LeadScoringEngine()

        behavior = VisitorBehavior(
            visitor_id="visitor_123",
            page_url="https://serbyn.pro/portfolio",
            time_on_page_seconds=120,
            scroll_depth_percent=85,
            utm_source="linkedin",
        )

        result = engine.track_visitor_behavior(behavior)

        assert result["success"] == True
        assert result["visitor_id"] == "visitor_123"
        assert "behavior_id" in result

    def test_calculate_lead_score_based_on_hiring_indicators(self):
        """Test lead scoring based on hiring manager behavior patterns"""
        engine = LeadScoringEngine()

        # Simulate hiring manager behavior
        behaviors = [
            VisitorBehavior(
                visitor_id="visitor_123",
                page_url="https://serbyn.pro/portfolio",
                time_on_page_seconds=300,  # Long engagement
                scroll_depth_percent=95,  # Read thoroughly
                utm_source="linkedin",
            ),
            VisitorBehavior(
                visitor_id="visitor_123",
                page_url="https://serbyn.pro/contact",
                time_on_page_seconds=60,
                scroll_depth_percent=100,
                utm_source="linkedin",
            ),
        ]

        score = engine.calculate_lead_score("visitor_123", behaviors)

        assert isinstance(score, LeadScore)
        assert score.total_score >= 70  # High score for hiring behavior
        assert score.hiring_manager_probability >= 0.8
        assert "linkedin_professional" in score.score_breakdown
        assert "portfolio_engagement" in score.score_breakdown

    def test_calculate_lead_score_developer_vs_hiring_manager(self):
        """Test that lead scoring differentiates between developers and hiring managers"""
        engine = LeadScoringEngine()

        # Developer behavior - technical focus
        dev_behaviors = [
            VisitorBehavior(
                visitor_id="dev_visitor",
                page_url="https://serbyn.pro/portfolio/mlops-pipeline",
                time_on_page_seconds=600,  # Very long technical read
                scroll_depth_percent=100,
                utm_source="devto",
            )
        ]

        # Hiring manager behavior - business focus
        hm_behaviors = [
            VisitorBehavior(
                visitor_id="hm_visitor",
                page_url="https://serbyn.pro/portfolio",
                time_on_page_seconds=180,  # Moderate engagement
                scroll_depth_percent=80,
                utm_source="linkedin",
            ),
            VisitorBehavior(
                visitor_id="hm_visitor",
                page_url="https://serbyn.pro/contact",
                time_on_page_seconds=90,
                scroll_depth_percent=100,
                utm_source="linkedin",
            ),
        ]

        dev_score = engine.calculate_lead_score("dev_visitor", dev_behaviors)
        hm_score = engine.calculate_lead_score("hm_visitor", hm_behaviors)

        # Hiring manager should have higher hiring probability
        assert (
            hm_score.hiring_manager_probability > dev_score.hiring_manager_probability
        )
        assert hm_score.visitor_type == "hiring_manager"
        assert dev_score.visitor_type == "developer"

    def test_identify_company_from_email_domain(self):
        """Test company identification from visitor email domain for lead qualification"""
        engine = LeadScoringEngine()

        # Test with known tech company
        company_info = engine.identify_company_from_domain("jane.doe@google.com")
        assert company_info["company_name"] == "Google"
        assert company_info["is_target_company"] == True
        assert company_info["company_size"] == "large"

        # Test with unknown company
        company_info = engine.identify_company_from_domain("john@smallstartup.com")
        assert company_info["company_name"] == "Unknown"
        assert company_info["is_target_company"] == False


class TestConversionFunnelTracking:
    """Test conversion funnel from content to job inquiry"""

    def test_track_content_view_to_website_visit(self):
        """Test tracking conversion from content platform to serbyn.pro"""
        tracker = ConversionFunnelTracker()

        conversion_event = ConversionEvent(
            event_type="content_to_website",
            source_platform="linkedin",
            source_content_url="https://linkedin.com/posts/vitaliiserbyn/mlops-case-study",
            destination_url="https://serbyn.pro/portfolio?utm_source=linkedin",
            visitor_id="visitor_123",
            timestamp=datetime.utcnow(),
        )

        result = tracker.track_conversion(conversion_event)

        assert result["success"] == True
        assert result["conversion_type"] == "content_to_website"
        assert result["source_platform"] == "linkedin"
        assert "conversion_id" in result

    def test_track_website_visit_to_job_inquiry(self):
        """Test tracking conversion from website visit to job inquiry"""
        tracker = ConversionFunnelTracker()

        conversion_event = ConversionEvent(
            event_type="website_to_inquiry",
            source_platform="serbyn.pro",
            source_content_url="https://serbyn.pro/contact",
            destination_url="contact_form_submission",
            visitor_id="visitor_123",
            timestamp=datetime.utcnow(),
            inquiry_details={
                "company": "TechCorp",
                "position": "Senior MLOps Engineer",
                "budget_range": "$150k-200k",
            },
        )

        result = tracker.track_conversion(conversion_event)

        assert result["success"] == True
        assert result["conversion_type"] == "website_to_inquiry"
        assert result["inquiry_qualified"] == True  # High-value inquiry
        assert "lead_score" in result

    def test_calculate_full_attribution_chain(self):
        """Test calculating full attribution from content to job offer"""
        tracker = ConversionFunnelTracker()

        # First, create some conversion events to have data for the chain
        content_event = ConversionEvent(
            event_type="content_to_website",
            source_platform="devto",
            source_content_url="https://dev.to/vitaliiserbyn/mlops-optimization?utm_campaign=pr_automation",
            destination_url="https://serbyn.pro/portfolio",
            visitor_id="visitor_123",
            timestamp=datetime.utcnow() - timedelta(hours=48),
        )

        inquiry_event = ConversionEvent(
            event_type="website_to_inquiry",
            source_platform="serbyn.pro",
            source_content_url="https://serbyn.pro/contact",
            destination_url="contact_form_submission",
            visitor_id="visitor_123",
            timestamp=datetime.utcnow(),
            inquiry_details={
                "company": "TechCorp",
                "position": "Senior MLOps Engineer",
                "budget_range": "$180k",
            },
        )

        # Track the conversion events
        tracker.track_conversion(content_event)
        tracker.track_conversion(inquiry_event)

        # Now calculate the attribution chain
        chain_result = tracker.calculate_attribution_chain("visitor_123")

        assert chain_result["original_content"] is not None
        assert chain_result["platform"] == "devto"
        assert chain_result["time_to_inquiry_hours"] >= 0
        assert chain_result["lead_score"] >= 0
        assert "conversion_probability" in chain_result
        assert chain_result["inquiry_value"] > 0

    def test_identify_conversion_bottlenecks(self):
        """Test identification of funnel drop-off points"""
        tracker = ConversionFunnelTracker()

        bottleneck_analysis = tracker.identify_conversion_bottlenecks()

        expected_structure = {
            "content_to_website": {"conversion_rate": 0.0, "drop_off_reasons": []},
            "website_to_contact": {"conversion_rate": 0.0, "drop_off_reasons": []},
            "contact_to_inquiry": {"conversion_rate": 0.0, "drop_off_reasons": []},
            "recommendations": [],
        }

        assert "content_to_website" in bottleneck_analysis
        assert "website_to_contact" in bottleneck_analysis
        assert "contact_to_inquiry" in bottleneck_analysis
        assert "recommendations" in bottleneck_analysis


class TestABTestingFramework:
    """Test A/B testing for conversion optimization"""

    def test_create_ab_test_with_variants(self):
        """Test creating an A/B test with different landing page variants"""
        framework = ABTestingFramework()

        variant_a = TestVariant(
            name="original_cta",
            description="Original 'Contact Me' button",
            changes={"cta_text": "Contact Me", "cta_color": "#0066cc"},
        )

        variant_b = TestVariant(
            name="hiring_optimized_cta",
            description="Hiring-focused 'Schedule Interview' button",
            changes={"cta_text": "Schedule Interview", "cta_color": "#00cc66"},
        )

        test_config = {
            "test_name": "contact_cta_optimization",
            "traffic_split": 0.5,  # 50/50 split
            "success_metric": "job_inquiry_conversion",
            "minimum_sample_size": 100,
        }

        result = framework.create_ab_test([variant_a, variant_b], test_config)

        assert result["success"] == True
        assert result["test_id"] is not None
        assert result["variants_created"] == 2
        assert result["traffic_split"] == 0.5

    def test_assign_visitor_to_test_group(self):
        """Test random assignment of visitors to A/B test groups"""
        framework = ABTestingFramework()

        # First create a test
        variant_a = TestVariant(
            name="original_cta",
            description="Original 'Contact Me' button",
            changes={"cta_text": "Contact Me", "cta_color": "#0066cc"},
        )

        variant_b = TestVariant(
            name="hiring_optimized_cta",
            description="Hiring-focused 'Schedule Interview' button",
            changes={"cta_text": "Schedule Interview", "cta_color": "#00cc66"},
        )

        test_config = {
            "test_name": "contact_cta_optimization_001",
            "traffic_split": 0.5,
            "success_metric": "job_inquiry_conversion",
            "minimum_sample_size": 100,
        }

        test_result = framework.create_ab_test([variant_a, variant_b], test_config)
        test_id = test_result["test_id"]
        visitor_id = "visitor_123"

        assignment = framework.assign_visitor_to_group(test_id, visitor_id)

        assert assignment["visitor_id"] == visitor_id
        assert assignment["test_id"] == test_id
        assert assignment["variant"] in ["variant_a", "variant_b"]
        assert assignment["assigned_at"] is not None

        # Test consistency - same visitor should get same assignment
        assignment2 = framework.assign_visitor_to_group(test_id, visitor_id)
        assert assignment["variant"] == assignment2["variant"]

    def test_track_ab_test_conversion(self):
        """Test tracking conversions for A/B test analysis"""
        framework = ABTestingFramework()

        # First create a test
        variant_a = TestVariant(
            name="original_cta",
            description="Original 'Contact Me' button",
            changes={"cta_text": "Contact Me", "cta_color": "#0066cc"},
        )

        variant_b = TestVariant(
            name="hiring_optimized_cta",
            description="Hiring-focused 'Schedule Interview' button",
            changes={"cta_text": "Schedule Interview", "cta_color": "#00cc66"},
        )

        test_config = {
            "test_name": "contact_cta_optimization_001",
            "traffic_split": 0.5,
            "success_metric": "job_inquiry_conversion",
            "minimum_sample_size": 100,
        }

        test_result = framework.create_ab_test([variant_a, variant_b], test_config)
        test_id = test_result["test_id"]

        conversion_data = {
            "test_id": test_id,
            "visitor_id": "visitor_123",
            "variant": "variant_b",
            "conversion_type": "job_inquiry",
            "conversion_value": 175000,  # Estimated job value
        }

        result = framework.track_conversion(conversion_data)

        assert result["success"] == True
        assert result["conversion_recorded"] == True
        assert result["variant"] == "variant_b"

    def test_calculate_ab_test_results_statistical_significance(self):
        """Test statistical analysis of A/B test results"""
        framework = ABTestingFramework()

        # First create a test
        variant_a = TestVariant(
            name="original_cta",
            description="Original 'Contact Me' button",
            changes={"cta_text": "Contact Me", "cta_color": "#0066cc"},
        )

        variant_b = TestVariant(
            name="hiring_optimized_cta",
            description="Hiring-focused 'Schedule Interview' button",
            changes={"cta_text": "Schedule Interview", "cta_color": "#00cc66"},
        )

        test_config = {
            "test_name": "contact_cta_optimization_001",
            "traffic_split": 0.5,
            "success_metric": "job_inquiry_conversion",
            "minimum_sample_size": 100,
        }

        test_result = framework.create_ab_test([variant_a, variant_b], test_config)
        test_id = test_result["test_id"]

        results = framework.calculate_test_results(test_id)

        assert results["test_id"] == test_id
        assert "variants" in results
        assert "statistical_significance" in results
        assert "recommended_action" in results
        assert "winner" in results

    def test_ab_test_early_stopping_criteria(self):
        """Test early stopping when one variant clearly wins"""
        framework = ABTestingFramework()

        # Simulate variant B significantly outperforming
        test_data = {
            "variant_a": {"conversions": 5, "visitors": 100, "conversion_rate": 0.05},
            "variant_b": {"conversions": 20, "visitors": 100, "conversion_rate": 0.20},
        }

        should_stop = framework.should_stop_test_early("test_001", test_data)

        assert should_stop["stop_early"] == True
        assert should_stop["reason"] == "statistical_significance_reached"
        assert should_stop["winner"] == "variant_b"
        assert should_stop["confidence_level"] >= 0.95


class TestIntegratedConversionOptimization:
    """Test integration of all components for end-to-end conversion optimization"""

    def test_complete_conversion_flow_linkedin_to_job_inquiry(self):
        """Test complete flow: LinkedIn post → serbyn.pro → job inquiry"""

        # This test will orchestrate all components together
        utm_processor = UTMParameterProcessor()
        lead_engine = LeadScoringEngine()
        funnel_tracker = ConversionFunnelTracker()
        ab_framework = ABTestingFramework()

        # Step 1: Visitor clicks LinkedIn UTM link
        utm_url = "https://serbyn.pro/portfolio?utm_source=linkedin&utm_medium=social&utm_campaign=pr_automation&utm_content=mlops_case_study"
        utm_params = utm_processor.extract_utm_parameters(utm_url)

        # Step 2: Track visitor behavior for lead scoring
        behavior = VisitorBehavior(
            visitor_id="visitor_123",
            page_url="https://serbyn.pro/portfolio",
            time_on_page_seconds=240,
            scroll_depth_percent=90,
            utm_source="linkedin",
        )
        lead_engine.track_visitor_behavior(behavior)

        # Step 3: Create A/B test first, then assign visitor
        variant_a = TestVariant(
            name="original_cta",
            description="Original 'Contact Me' button",
            changes={"cta_text": "Contact Me"},
        )
        variant_b = TestVariant(
            name="hiring_cta",
            description="Hiring-focused 'Schedule Interview' button",
            changes={"cta_text": "Schedule Interview"},
        )
        test_config = {
            "test_name": "contact_cta_test",
            "traffic_split": 0.5,
            "success_metric": "job_inquiry_conversion",
        }
        ab_test_result = ab_framework.create_ab_test(
            [variant_a, variant_b], test_config
        )
        ab_assignment = ab_framework.assign_visitor_to_group(
            ab_test_result["test_id"], "visitor_123"
        )

        # Step 4: Track initial content-to-website conversion
        initial_conversion = ConversionEvent(
            event_type="content_to_website",
            source_platform="linkedin",
            source_content_url="https://linkedin.com/posts/vitaliiserbyn/mlops-case-study?utm_campaign=pr_automation",
            destination_url=utm_url,
            visitor_id="visitor_123",
            timestamp=datetime.utcnow() - timedelta(hours=1),
        )
        funnel_tracker.track_conversion(initial_conversion)

        # Step 5: Track conversion through funnel to job inquiry
        conversion = ConversionEvent(
            event_type="website_to_inquiry",
            source_platform="serbyn.pro",
            source_content_url="https://serbyn.pro/contact",
            destination_url="contact_form_submission",
            visitor_id="visitor_123",
            timestamp=datetime.utcnow(),
            inquiry_details={
                "position": "Senior MLOps Engineer",
                "company": "TechCorp",
            },
        )
        funnel_result = funnel_tracker.track_conversion(conversion)

        # Step 6: Calculate final attribution and ROI
        attribution = funnel_tracker.calculate_attribution_chain("visitor_123")

        # Verify integrated results
        assert utm_params["utm_source"] == "linkedin"
        assert funnel_result["success"] == True
        assert attribution["platform"] == "linkedin"
        assert ab_assignment["variant"] in ["variant_a", "variant_b"]

        # Verify conversion value tracking
        assert attribution["inquiry_value"] > 0
        assert attribution["conversion_probability"] > 0.5


# These tests will fail initially because we haven't implemented the classes yet
# This follows TDD principles: Red → Green → Refactor
