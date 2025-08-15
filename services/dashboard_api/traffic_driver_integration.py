"""
Traffic Driver Integration - Complete UTM tracking and lead scoring integration

This module integrates the UTM tracking, lead scoring, conversion funnel, and A/B testing
components with the existing unified analytics system to maximize conversion from content
to job opportunities.

Features:
1. UTM parameter processing and analytics
2. Lead scoring based on visitor behavior
3. Conversion funnel tracking from content to job inquiry
4. A/B testing for conversion optimization
5. Integration with existing auto_content_pipeline for maximum ROI
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from utm_tracker import UTMParameterProcessor
from lead_scoring import LeadScoringEngine, VisitorBehavior
from conversion_funnel import ConversionFunnelTracker, ConversionEvent
from ab_testing import ABTestingFramework, TestVariant
from unified_analytics import AnalyticsAggregationService


class TrafficDriverService:
    """
    Complete traffic driver service for maximizing job opportunity conversions.
    
    Integrates all conversion optimization components to turn content traffic
    into qualified job leads and opportunities.
    """
    
    def __init__(self):
        self.utm_processor = UTMParameterProcessor()
        self.lead_engine = LeadScoringEngine()
        self.funnel_tracker = ConversionFunnelTracker()
        self.ab_framework = ABTestingFramework()
        self.analytics_service = AnalyticsAggregationService()
        
        # Track key metrics for conversion optimization
        self.conversion_metrics = {
            "content_clicks": 0,
            "website_visits": 0,
            "contact_page_visits": 0,
            "job_inquiries": 0,
            "qualified_leads": 0
        }
    
    async def track_visitor_from_content(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a visitor coming from content with UTM parameters.
        
        Args:
            visitor_data: Dictionary containing visitor info and UTM URL
            
        Returns:
            Dictionary with tracking results and visitor assignment
        """
        # Step 1: Extract and validate UTM parameters
        utm_url = visitor_data.get("referrer_url", "")
        utm_params = self.utm_processor.extract_utm_parameters(utm_url)
        
        if utm_params:
            try:
                self.utm_processor.validate_utm_parameters(utm_params)
            except Exception as e:
                return {"error": f"Invalid UTM parameters: {str(e)}"}
        
        # Step 2: Store UTM analytics
        visitor_info = {
            "ip_address": visitor_data.get("ip_address", "unknown"),
            "user_agent": visitor_data.get("user_agent", "unknown"),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        utm_tracking = self.utm_processor.store_utm_analytics(utm_params, visitor_info)
        
        # Step 3: Track conversion funnel event
        if utm_params.get("utm_source"):
            conversion_event = ConversionEvent(
                event_type="content_to_website",
                source_platform=utm_params["utm_source"],
                source_content_url=utm_url,
                destination_url=visitor_data.get("current_url", "https://serbyn.pro"),
                visitor_id=visitor_data["visitor_id"],
                timestamp=datetime.utcnow()
            )
            self.funnel_tracker.track_conversion(conversion_event)
        
        # Step 4: Assign to active A/B tests
        ab_assignments = []
        for test_id in self.ab_framework.active_tests.keys():
            assignment = self.ab_framework.assign_visitor_to_group(test_id, visitor_data["visitor_id"])
            if "error" not in assignment:
                ab_assignments.append(assignment)
        
        # Update metrics
        self.conversion_metrics["content_clicks"] += 1
        self.conversion_metrics["website_visits"] += 1
        
        return {
            "success": True,
            "utm_tracking": utm_tracking,
            "ab_assignments": ab_assignments,
            "platform": utm_params.get("utm_source", "direct"),
            "campaign": utm_params.get("utm_campaign", "unknown")
        }
    
    async def track_page_behavior(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track visitor behavior on website pages for lead scoring.
        
        Args:
            behavior_data: Dictionary with page behavior information
            
        Returns:
            Dictionary with behavior tracking and lead score
        """
        # Create behavior record
        behavior = VisitorBehavior(
            visitor_id=behavior_data["visitor_id"],
            page_url=behavior_data["page_url"],
            time_on_page_seconds=behavior_data.get("time_on_page_seconds", 0),
            scroll_depth_percent=behavior_data.get("scroll_depth_percent", 0),
            utm_source=behavior_data.get("utm_source", "direct")
        )
        
        # Track behavior
        track_result = self.lead_engine.track_visitor_behavior(behavior)
        
        # Calculate updated lead score
        visitor_behaviors = [behavior]  # In production, get all behaviors for visitor
        lead_score = self.lead_engine.calculate_lead_score(
            behavior_data["visitor_id"], 
            visitor_behaviors
        )
        
        # Track contact page visits
        if "contact" in behavior_data["page_url"]:
            self.conversion_metrics["contact_page_visits"] += 1
        
        return {
            "success": True,
            "behavior_tracked": track_result["success"],
            "lead_score": {
                "total_score": lead_score.total_score,
                "hiring_manager_probability": lead_score.hiring_manager_probability,
                "visitor_type": lead_score.visitor_type,
                "score_breakdown": lead_score.score_breakdown
            }
        }
    
    async def track_job_inquiry(self, inquiry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a job inquiry conversion.
        
        Args:
            inquiry_data: Dictionary with job inquiry details
            
        Returns:
            Dictionary with conversion tracking and attribution
        """
        # Track conversion funnel event
        conversion_event = ConversionEvent(
            event_type="website_to_inquiry",
            source_platform="serbyn.pro",
            source_content_url=inquiry_data.get("source_page", "https://serbyn.pro/contact"),
            destination_url="job_inquiry_form",
            visitor_id=inquiry_data["visitor_id"],
            timestamp=datetime.utcnow(),
            inquiry_details=inquiry_data.get("inquiry_details", {})
        )
        
        funnel_result = self.funnel_tracker.track_conversion(conversion_event)
        
        # Track A/B test conversion
        visitor_assignments = self.ab_framework.test_assignments.get(inquiry_data["visitor_id"], {})
        for test_id, variant in visitor_assignments.items():
            conversion_data = {
                "test_id": test_id,
                "visitor_id": inquiry_data["visitor_id"],
                "variant": variant,
                "conversion_type": "job_inquiry",
                "conversion_value": inquiry_data.get("estimated_value", 150000)
            }
            self.ab_framework.track_conversion(conversion_data)
        
        # Calculate full attribution
        attribution = self.funnel_tracker.calculate_attribution_chain(inquiry_data["visitor_id"])
        
        # Update metrics
        self.conversion_metrics["job_inquiries"] += 1
        if funnel_result.get("inquiry_qualified", False):
            self.conversion_metrics["qualified_leads"] += 1
        
        return {
            "success": True,
            "conversion_tracked": funnel_result["success"],
            "attribution": attribution,
            "lead_qualified": funnel_result.get("inquiry_qualified", False),
            "estimated_value": funnel_result.get("estimated_value", 0)
        }
    
    async def get_conversion_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive conversion analytics and optimization insights.
        
        Returns:
            Dictionary with complete conversion funnel analytics
        """
        # Platform analytics
        platform_metrics = await self.analytics_service.collect_all_platform_metrics()
        conversion_summary = await self.analytics_service.calculate_conversion_summary(platform_metrics)
        
        # Conversion funnel analysis
        bottleneck_analysis = self.funnel_tracker.identify_conversion_bottlenecks()
        
        # A/B test results
        ab_test_results = {}
        for test_id in self.ab_framework.active_tests.keys():
            ab_test_results[test_id] = self.ab_framework.calculate_test_results(test_id)
        
        # Calculate conversion rates
        total_visitors = max(self.conversion_metrics["website_visits"], 1)
        conversion_rates = {
            "content_to_website": 1.0,  # 100% by definition
            "website_to_contact": self.conversion_metrics["contact_page_visits"] / total_visitors,
            "contact_to_inquiry": self.conversion_metrics["job_inquiries"] / max(self.conversion_metrics["contact_page_visits"], 1),
            "overall_conversion": self.conversion_metrics["job_inquiries"] / total_visitors
        }
        
        # ROI calculation
        estimated_total_value = self.conversion_metrics["qualified_leads"] * 175000  # Average job value
        content_creation_cost = 2000  # Estimated monthly content cost
        roi_percentage = ((estimated_total_value - content_creation_cost) / content_creation_cost * 100) if content_creation_cost > 0 else 0
        
        return {
            "platform_analytics": conversion_summary,
            "conversion_funnel": {
                "metrics": self.conversion_metrics,
                "conversion_rates": conversion_rates,
                "bottleneck_analysis": bottleneck_analysis
            },
            "ab_test_results": ab_test_results,
            "roi_analysis": {
                "total_estimated_value": estimated_total_value,
                "content_investment": content_creation_cost,
                "roi_percentage": roi_percentage,
                "cost_per_lead": content_creation_cost / max(self.conversion_metrics["qualified_leads"], 1)
            },
            "optimization_recommendations": self._generate_optimization_recommendations(conversion_rates, bottleneck_analysis)
        }
    
    async def create_conversion_optimization_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new A/B test for conversion optimization.
        
        Args:
            test_config: Configuration for the A/B test
            
        Returns:
            Dictionary with test creation result
        """
        # Pre-configured high-impact test variants
        if test_config["test_type"] == "contact_cta":
            variants = [
                TestVariant(
                    name="original",
                    description="Current contact CTA",
                    changes={"cta_text": "Contact Me", "cta_color": "#0066cc"}
                ),
                TestVariant(
                    name="hiring_focused",
                    description="Hiring-focused CTA",
                    changes={"cta_text": "Let's Discuss Your AI Needs", "cta_color": "#00cc66"}
                )
            ]
        elif test_config["test_type"] == "portfolio_layout":
            variants = [
                TestVariant(
                    name="technical_first",
                    description="Technical details first",
                    changes={"layout": "technical_first", "sections": ["tech", "business", "contact"]}
                ),
                TestVariant(
                    name="business_first", 
                    description="Business impact first",
                    changes={"layout": "business_first", "sections": ["business", "tech", "contact"]}
                )
            ]
        else:
            return {"error": "Unsupported test type"}
        
        return self.ab_framework.create_ab_test(variants, test_config)
    
    def _generate_optimization_recommendations(self, conversion_rates: Dict[str, float], bottleneck_analysis: Dict[str, Any]) -> List[str]:
        """Generate specific optimization recommendations based on data"""
        
        recommendations = []
        
        # Content to website optimization
        if conversion_rates["website_to_contact"] < 0.15:
            recommendations.append("Improve website UX and add more compelling portfolio CTAs to increase contact page visits")
        
        # Contact optimization
        if conversion_rates["contact_to_inquiry"] < 0.25:
            recommendations.append("Simplify contact form and add social proof to increase inquiry conversion")
        
        # Overall conversion optimization
        if conversion_rates["overall_conversion"] < 0.05:
            recommendations.append("Focus on targeting hiring managers specifically - current traffic may be too developer-heavy")
        
        # A/B testing recommendations
        active_tests = len(self.ab_framework.active_tests)
        if active_tests == 0:
            recommendations.append("Start A/B testing different CTAs and page layouts to optimize conversion rates")
        
        # Content strategy recommendations
        recommendations.append("Continue creating authority-building content with business impact focus for hiring managers")
        
        return recommendations


# Example usage and integration
class ContentToJobOpportunityPipeline:
    """
    Complete pipeline from content creation to job opportunity conversion.
    
    Integrates with the existing auto_content_pipeline to create a 
    comprehensive content marketing system optimized for job acquisition.
    """
    
    def __init__(self):
        self.traffic_driver = TrafficDriverService()
    
    async def process_content_visitor(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a visitor from content through the complete conversion pipeline.
        
        This is the main entry point for content-driven traffic.
        """
        # Track initial visit
        tracking_result = await self.traffic_driver.track_visitor_from_content(visitor_data)
        
        if not tracking_result.get("success"):
            return tracking_result
        
        # Simulate page behavior tracking (in production, this would be triggered by frontend)
        behavior_data = {
            "visitor_id": visitor_data["visitor_id"],
            "page_url": visitor_data.get("current_url", "https://serbyn.pro/portfolio"),
            "time_on_page_seconds": 180,  # Simulated engagement
            "scroll_depth_percent": 85,
            "utm_source": tracking_result.get("platform", "direct")
        }
        
        behavior_result = await self.traffic_driver.track_page_behavior(behavior_data)
        
        return {
            "visitor_tracked": tracking_result["success"],
            "platform": tracking_result["platform"],
            "campaign": tracking_result["campaign"],
            "lead_score": behavior_result["lead_score"],
            "conversion_potential": behavior_result["lead_score"]["hiring_manager_probability"]
        }
    
    async def get_campaign_performance(self) -> Dict[str, Any]:
        """Get complete campaign performance metrics"""
        return await self.traffic_driver.get_conversion_analytics()