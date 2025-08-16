"""
Lead Scoring Engine for Visitor Behavior Analysis

This module implements lead scoring based on visitor behavior patterns
to identify high-potential hiring managers and qualified leads.

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class VisitorBehavior:
    """Represents a single visitor behavior event"""

    visitor_id: str
    page_url: str
    time_on_page_seconds: int
    scroll_depth_percent: int
    utm_source: str
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class LeadScore:
    """Represents a calculated lead score with breakdown"""

    visitor_id: str
    total_score: int
    hiring_manager_probability: float
    visitor_type: str
    score_breakdown: Dict[str, int]
    calculated_at: datetime


class LeadScoringEngine:
    """
    Engine for scoring leads based on visitor behavior patterns.

    Analyzes visitor behavior to identify hiring managers vs developers
    and calculate lead quality scores for conversion optimization.
    """

    def __init__(self):
        # In-memory storage for TDD - will replace with database later
        self.behavior_store = {}
        self.company_database = {
            # Known tech companies for lead qualification
            "google.com": {
                "company_name": "Google",
                "is_target_company": True,
                "company_size": "large",
            },
            "microsoft.com": {
                "company_name": "Microsoft",
                "is_target_company": True,
                "company_size": "large",
            },
            "amazon.com": {
                "company_name": "Amazon",
                "is_target_company": True,
                "company_size": "large",
            },
            "meta.com": {
                "company_name": "Meta",
                "is_target_company": True,
                "company_size": "large",
            },
            "netflix.com": {
                "company_name": "Netflix",
                "is_target_company": True,
                "company_size": "large",
            },
            "uber.com": {
                "company_name": "Uber",
                "is_target_company": True,
                "company_size": "large",
            },
            "stripe.com": {
                "company_name": "Stripe",
                "is_target_company": True,
                "company_size": "medium",
            },
        }

    def track_visitor_behavior(self, behavior: VisitorBehavior) -> Dict[str, Any]:
        """
        Track visitor behavior for lead scoring analysis.

        Args:
            behavior: VisitorBehavior instance with visitor activity data

        Returns:
            Dictionary with tracking result and behavior ID
        """
        # Generate behavior ID
        behavior_id = f"behavior_{len(self.behavior_store) + 1:06d}"

        # Store behavior record
        if behavior.visitor_id not in self.behavior_store:
            self.behavior_store[behavior.visitor_id] = []

        behavior_record = {
            "behavior_id": behavior_id,
            "visitor_id": behavior.visitor_id,
            "page_url": behavior.page_url,
            "time_on_page_seconds": behavior.time_on_page_seconds,
            "scroll_depth_percent": behavior.scroll_depth_percent,
            "utm_source": behavior.utm_source,
            "timestamp": behavior.timestamp,
        }

        self.behavior_store[behavior.visitor_id].append(behavior_record)

        return {
            "success": True,
            "visitor_id": behavior.visitor_id,
            "behavior_id": behavior_id,
        }

    def calculate_lead_score(
        self, visitor_id: str, behaviors: List[VisitorBehavior]
    ) -> LeadScore:
        """
        Calculate lead score based on visitor behavior patterns.

        Args:
            visitor_id: Unique visitor identifier
            behaviors: List of visitor behaviors to analyze

        Returns:
            LeadScore with total score and breakdown
        """
        score = 0
        score_breakdown = {}

        # Analyze behaviors for scoring
        total_time = sum(b.time_on_page_seconds for b in behaviors)
        avg_scroll_depth = sum(b.scroll_depth_percent for b in behaviors) / len(
            behaviors
        )

        # LinkedIn source indicates professional context (hiring manager behavior)
        linkedin_behaviors = [b for b in behaviors if b.utm_source == "linkedin"]
        if linkedin_behaviors:
            linkedin_score = len(linkedin_behaviors) * 15
            score += linkedin_score
            score_breakdown["linkedin_professional"] = linkedin_score

        # Portfolio page engagement indicates hiring interest
        portfolio_behaviors = [b for b in behaviors if "portfolio" in b.page_url]
        if portfolio_behaviors:
            portfolio_time = sum(b.time_on_page_seconds for b in portfolio_behaviors)
            if portfolio_time > 180:  # 3+ minutes on portfolio
                portfolio_score = 25
                score += portfolio_score
                score_breakdown["portfolio_engagement"] = portfolio_score

        # Contact page visit indicates hiring intent
        contact_behaviors = [b for b in behaviors if "contact" in b.page_url]
        if contact_behaviors:
            contact_score = 30
            score += contact_score
            score_breakdown["contact_intent"] = contact_score

        # High engagement patterns (but differentiate technical vs business engagement)
        technical_behaviors = [
            b for b in behaviors if ("mlops" in b.page_url or "technical" in b.page_url)
        ]
        business_behaviors = [
            b
            for b in behaviors
            if ("portfolio" in b.page_url and "mlops" not in b.page_url)
            or "contact" in b.page_url
        ]

        if total_time > 300:  # 5+ minutes total
            if technical_behaviors and not business_behaviors:
                # Long technical engagement suggests developer
                engagement_score = 10  # Lower score for developer behavior
            else:
                # Business engagement suggests hiring manager
                engagement_score = 20
            score += engagement_score
            score_breakdown["high_engagement"] = engagement_score

        if avg_scroll_depth > 80:  # Read thoroughly
            depth_score = 15
            score += depth_score
            score_breakdown["content_depth"] = depth_score

        # Determine visitor type and hiring probability
        hiring_manager_probability = self._calculate_hiring_probability(
            behaviors, score
        )
        visitor_type = self._classify_visitor_type(
            behaviors, hiring_manager_probability
        )

        return LeadScore(
            visitor_id=visitor_id,
            total_score=score,
            hiring_manager_probability=hiring_manager_probability,
            visitor_type=visitor_type,
            score_breakdown=score_breakdown,
            calculated_at=datetime.utcnow(),
        )

    def _calculate_hiring_probability(
        self, behaviors: List[VisitorBehavior], score: int
    ) -> float:
        """Calculate probability that visitor is a hiring manager"""

        # Base probability from score
        base_prob = min(score / 100.0, 1.0)

        # Boost for hiring-specific behaviors
        contact_visits = len([b for b in behaviors if "contact" in b.page_url])
        linkedin_source = any(b.utm_source == "linkedin" for b in behaviors)
        portfolio_focus = any(
            "portfolio" in b.page_url and b.time_on_page_seconds > 120
            for b in behaviors
        )

        if contact_visits > 0 and linkedin_source and portfolio_focus:
            return min(base_prob + 0.3, 1.0)  # High confidence hiring manager
        elif contact_visits > 0 and linkedin_source:
            return min(base_prob + 0.2, 1.0)  # Likely hiring manager
        elif linkedin_source and portfolio_focus:
            return min(base_prob + 0.1, 1.0)  # Possible hiring manager

        return base_prob

    def _classify_visitor_type(
        self, behaviors: List[VisitorBehavior], hiring_probability: float
    ) -> str:
        """Classify visitor as developer, hiring_manager, or recruiter"""

        # Strong hiring manager indicators
        contact_visits = len([b for b in behaviors if "contact" in b.page_url])
        linkedin_source = any(b.utm_source == "linkedin" for b in behaviors)

        if hiring_probability >= 0.7 or (contact_visits > 0 and linkedin_source):
            return "hiring_manager"

        # Developer patterns: technical content focus, dev.to source, very long technical reads
        devto_behaviors = any(b.utm_source == "devto" for b in behaviors)
        technical_focus = any(
            "mlops" in b.page_url or "technical" in b.page_url for b in behaviors
        )
        long_technical_reads = any(
            b.time_on_page_seconds > 400 for b in behaviors
        )  # Very long reads
        no_contact_page = not any("contact" in b.page_url for b in behaviors)

        # If strong developer signals and no hiring behavior, classify as developer
        if (
            (devto_behaviors or technical_focus or long_technical_reads)
            and no_contact_page
            and hiring_probability < 0.6
        ):
            return "developer"

        # Default classification based on probability
        if hiring_probability >= 0.4:
            return "hiring_manager"
        else:
            return "developer"

    def identify_company_from_domain(self, email: str) -> Dict[str, Any]:
        """
        Identify company information from email domain.

        Args:
            email: Visitor email address

        Returns:
            Dictionary with company information and target qualification
        """
        if "@" not in email:
            return {
                "company_name": "Unknown",
                "is_target_company": False,
                "company_size": "unknown",
            }

        domain = email.split("@")[1].lower()

        # Check known companies
        if domain in self.company_database:
            return self.company_database[domain]

        # Default for unknown companies
        return {
            "company_name": "Unknown",
            "is_target_company": False,
            "company_size": "unknown",
        }

    def get_visitor_behaviors(self, visitor_id: str) -> List[Dict[str, Any]]:
        """Get all tracked behaviors for a visitor"""
        return self.behavior_store.get(visitor_id, [])
