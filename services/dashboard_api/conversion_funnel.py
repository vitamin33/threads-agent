"""
Conversion Funnel Tracking for Content Attribution

This module tracks conversions through the complete funnel:
Content View → Website Visit → Contact → Job Inquiry

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid


@dataclass
class ConversionEvent:
    """Represents a conversion event in the funnel"""
    event_type: str  # "content_to_website", "website_to_inquiry", etc.
    source_platform: str
    source_content_url: str
    destination_url: str
    visitor_id: str
    timestamp: datetime
    inquiry_details: Optional[Dict[str, Any]] = None


class ConversionFunnelTracker:
    """
    Tracks conversions through the complete marketing funnel.
    
    Provides attribution analysis from content to job inquiries
    and identifies conversion bottlenecks for optimization.
    """
    
    def __init__(self):
        # In-memory storage for TDD - will replace with database later
        self.conversion_store = {}
        self.visitor_journeys = {}  # Track complete visitor journeys
        
        # Define high-value inquiry criteria
        self.high_value_keywords = {
            "senior", "lead", "principal", "staff", "manager", "director",
            "150k", "160k", "170k", "180k", "190k", "200k", "$150", "$160", "$170", "$180", "$190", "$200"
        }
    
    def track_conversion(self, conversion_event: ConversionEvent) -> Dict[str, Any]:
        """
        Track a conversion event in the funnel.
        
        Args:
            conversion_event: ConversionEvent instance with conversion data
            
        Returns:
            Dictionary with tracking result and conversion analysis
        """
        # Generate conversion ID
        conversion_id = str(uuid.uuid4())
        
        # Store conversion record
        conversion_record = {
            "conversion_id": conversion_id,
            "event_type": conversion_event.event_type,
            "source_platform": conversion_event.source_platform,
            "source_content_url": conversion_event.source_content_url,
            "destination_url": conversion_event.destination_url,
            "visitor_id": conversion_event.visitor_id,
            "timestamp": conversion_event.timestamp,
            "inquiry_details": conversion_event.inquiry_details
        }
        
        self.conversion_store[conversion_id] = conversion_record
        
        # Update visitor journey
        if conversion_event.visitor_id not in self.visitor_journeys:
            self.visitor_journeys[conversion_event.visitor_id] = []
        
        self.visitor_journeys[conversion_event.visitor_id].append(conversion_record)
        
        # Analyze conversion
        result = {
            "success": True,
            "conversion_id": conversion_id,
            "conversion_type": conversion_event.event_type,
            "source_platform": conversion_event.source_platform
        }
        
        # Add special analysis for job inquiries
        if conversion_event.event_type == "website_to_inquiry" and conversion_event.inquiry_details:
            inquiry_analysis = self._analyze_inquiry_quality(conversion_event.inquiry_details)
            result.update(inquiry_analysis)
        
        return result
    
    def _analyze_inquiry_quality(self, inquiry_details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality and value of a job inquiry"""
        
        # Check for high-value indicators
        inquiry_text = f"{inquiry_details.get('position', '')} {inquiry_details.get('company', '')} {inquiry_details.get('budget_range', '')}".lower()
        
        is_qualified = any(keyword in inquiry_text for keyword in self.high_value_keywords)
        
        # Estimate inquiry value based on position and budget
        estimated_value = self._estimate_inquiry_value(inquiry_details)
        
        # Calculate basic lead score (will be enhanced by LeadScoringEngine)
        lead_score = 70 if is_qualified else 40
        if "senior" in inquiry_text or "lead" in inquiry_text:
            lead_score += 15
        if any(budget in inquiry_text for budget in ["150k", "160k", "170k", "180k", "190k", "200k"]):
            lead_score += 20
        
        return {
            "inquiry_qualified": is_qualified,
            "estimated_value": estimated_value,
            "lead_score": min(lead_score, 100)
        }
    
    def _estimate_inquiry_value(self, inquiry_details: Dict[str, Any]) -> int:
        """Estimate the value of a job inquiry based on position and budget"""
        
        position = inquiry_details.get("position", "").lower()
        budget_range = inquiry_details.get("budget_range", "").lower()
        
        # Base value
        base_value = 120000  # Base engineer salary
        
        # Position multipliers
        if "senior" in position:
            base_value = 160000
        elif "lead" in position or "staff" in position:
            base_value = 180000
        elif "principal" in position or "manager" in position:
            base_value = 200000
        elif "director" in position:
            base_value = 250000
        
        # Extract budget if mentioned
        if "$" in budget_range:
            try:
                # Simple extraction - can be enhanced
                import re
                budget_match = re.search(r'\$(\d+)k?', budget_range)
                if budget_match:
                    budget_num = int(budget_match.group(1))
                    if budget_num > 1000:  # Already in dollars
                        return budget_num
                    else:  # In thousands
                        return budget_num * 1000
            except:
                pass
        
        return base_value
    
    def calculate_attribution_chain(self, visitor_id: str) -> Dict[str, Any]:
        """
        Calculate full attribution chain for a visitor.
        
        Args:
            visitor_id: Unique visitor identifier
            
        Returns:
            Dictionary with complete attribution analysis
        """
        visitor_journey = self.visitor_journeys.get(visitor_id, [])
        
        if not visitor_journey:
            return {"error": "No journey found for visitor"}
        
        # Find original content source
        first_conversion = visitor_journey[0]
        original_content = first_conversion.get("source_content_url", "unknown")
        platform = first_conversion.get("source_platform", "unknown")
        
        # Extract UTM campaign if available
        utm_campaign = "unknown"
        if "utm_campaign=" in original_content:
            try:
                utm_campaign = original_content.split("utm_campaign=")[1].split("&")[0]
            except:
                pass
        
        # Calculate journey metrics
        website_visits = len([c for c in visitor_journey if c["event_type"] == "content_to_website"])
        pages_viewed = list(set([c["destination_url"] for c in visitor_journey]))
        
        # Calculate time to inquiry
        time_to_inquiry_hours = 0
        inquiry_conversions = [c for c in visitor_journey if c["event_type"] == "website_to_inquiry"]
        if inquiry_conversions and visitor_journey:
            first_visit = visitor_journey[0]["timestamp"]
            first_inquiry = inquiry_conversions[0]["timestamp"]
            time_delta = first_inquiry - first_visit
            time_to_inquiry_hours = time_delta.total_seconds() / 3600
        
        # Calculate conversion probability based on journey
        conversion_probability = self._calculate_conversion_probability(visitor_journey)
        
        # Get inquiry value if available
        inquiry_value = 0
        lead_score = 0
        if inquiry_conversions:
            last_inquiry = inquiry_conversions[-1]
            inquiry_details = last_inquiry.get("inquiry_details", {})
            if inquiry_details:
                inquiry_value = self._estimate_inquiry_value(inquiry_details)
                analysis = self._analyze_inquiry_quality(inquiry_details)
                lead_score = analysis.get("lead_score", 0)
        
        return {
            "original_content": original_content,
            "platform": platform,
            "utm_campaign": utm_campaign,
            "website_visits": website_visits,
            "pages_viewed": pages_viewed,
            "time_to_inquiry_hours": time_to_inquiry_hours,
            "lead_score": lead_score,
            "inquiry_value": inquiry_value,
            "conversion_probability": conversion_probability
        }
    
    def _calculate_conversion_probability(self, visitor_journey: List[Dict[str, Any]]) -> float:
        """Calculate conversion probability based on visitor journey"""
        
        if not visitor_journey:
            return 0.0
        
        base_probability = 0.1  # 10% base conversion rate
        
        # Boost for multiple visits
        if len(visitor_journey) > 1:
            base_probability += 0.2
        
        # Boost for contact page visits
        contact_visits = len([c for c in visitor_journey if "contact" in c.get("destination_url", "")])
        if contact_visits > 0:
            base_probability += 0.3
        
        # Boost for portfolio engagement
        portfolio_visits = len([c for c in visitor_journey if "portfolio" in c.get("destination_url", "")])
        if portfolio_visits > 0:
            base_probability += 0.2
        
        # Boost for actual inquiries
        inquiry_count = len([c for c in visitor_journey if c["event_type"] == "website_to_inquiry"])
        if inquiry_count > 0:
            base_probability = 0.9  # High probability if already converted
        
        return min(base_probability, 1.0)
    
    def identify_conversion_bottlenecks(self) -> Dict[str, Any]:
        """
        Identify bottlenecks in the conversion funnel.
        
        Returns:
            Dictionary with conversion rates and bottleneck analysis
        """
        # Analyze all conversions to find drop-off points
        all_conversions = list(self.conversion_store.values())
        
        # Calculate conversion rates for each funnel stage
        content_to_website = len([c for c in all_conversions if c["event_type"] == "content_to_website"])
        website_to_contact = len([c for c in all_conversions if "contact" in c["destination_url"]])
        contact_to_inquiry = len([c for c in all_conversions if c["event_type"] == "website_to_inquiry"])
        
        # Calculate rates (avoid division by zero)
        total_visitors = max(len(self.visitor_journeys), 1)
        content_website_rate = content_to_website / total_visitors
        website_contact_rate = website_to_contact / max(content_to_website, 1)
        contact_inquiry_rate = contact_to_inquiry / max(website_to_contact, 1)
        
        # Identify bottlenecks and recommendations
        recommendations = []
        
        if content_website_rate < 0.1:
            recommendations.append("Improve content engagement and CTAs to drive more website traffic")
        
        if website_contact_rate < 0.2:
            recommendations.append("Optimize website UX and add more compelling contact CTAs")
        
        if contact_inquiry_rate < 0.3:
            recommendations.append("Simplify contact forms and add value propositions")
        
        return {
            "content_to_website": {
                "conversion_rate": content_website_rate,
                "drop_off_reasons": ["Low content engagement", "Weak CTAs"]
            },
            "website_to_contact": {
                "conversion_rate": website_contact_rate,
                "drop_off_reasons": ["Poor website UX", "Unclear value proposition"]
            },
            "contact_to_inquiry": {
                "conversion_rate": contact_inquiry_rate,
                "drop_off_reasons": ["Complex forms", "Lack of trust signals"]
            },
            "recommendations": recommendations
        }