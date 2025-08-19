"""
Revenue Attribution Dashboard Engine

Tracks the complete pipeline from content creation to job offers,
measuring ROI of the automated marketing system.

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ContentAttribution:
    """Represents content with attribution tracking"""

    content_id: str
    platform: str
    total_visitors: int = 0
    qualified_leads: int = 0
    job_offers: int = 0
    revenue_amount: float = 0
    content_creation_cost: float = 0
    roi_percentage: float = 0
    attribution_confidence: float = 0


class RevenueAttributionEngine:
    """
    Engine for tracking complete revenue attribution from content to job offers.

    Tracks: Content Creation → Traffic → Lead Qualification → Interview Pipeline → Job Offers → Revenue
    """

    def __init__(self):
        """Initialize the revenue attribution engine with data storage"""
        # In-memory storage for TDD - will replace with database later
        self.content_store = {}
        self.traffic_store = {}
        self.leads_store = {}
        self.interviews_store = {}
        self.offers_store = {}
        self.attribution_chains = {}

    def track_content_creation(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track content creation with cost and attribution setup.

        Args:
            content_data: Content information including costs and tracking details

        Returns:
            Dictionary with tracking confirmation and content ID
        """
        content_id = content_data["content_id"]

        # Calculate creation cost
        creation_cost = 0
        if "creation_cost_hours" in content_data and "hourly_rate" in content_data:
            creation_cost = (
                content_data["creation_cost_hours"] * content_data["hourly_rate"]
            )

        # Store content record
        self.content_store[content_id] = {
            "content_id": content_id,
            "platform": content_data["platform"],
            "content_type": content_data.get("content_type", "post"),
            "topic": content_data.get("topic", ""),
            "utm_campaign": content_data.get("utm_campaign", ""),
            "published_at": content_data.get("published_at", datetime.utcnow()),
            "creation_cost": creation_cost,
            "total_visitors": 0,
            "qualified_leads": 0,
            "job_offers": 0,
            "revenue_amount": 0,
        }

        # Initialize attribution chain
        self.attribution_chains[content_id] = {
            "content_id": content_id,
            "visitors": [],
            "leads": [],
            "offers": [],
        }

        return {"success": True, "content_id": content_id, "tracking_enabled": True}

    def track_content_traffic(self, visitor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track traffic from content with attribution linking.

        Args:
            visitor_data: Visitor information with source content and UTM data

        Returns:
            Dictionary with attribution linking confirmation
        """
        visitor_id = visitor_data["visitor_id"]
        source_content_id = visitor_data["source_content_id"]

        # Store traffic record
        traffic_key = f"{visitor_id}_{source_content_id}"
        self.traffic_store[traffic_key] = {
            "visitor_id": visitor_id,
            "source_content_id": source_content_id,
            "utm_source": visitor_data.get("utm_source", ""),
            "utm_campaign": visitor_data.get("utm_campaign", ""),
            "timestamp": visitor_data.get("timestamp", datetime.utcnow()),
        }

        # Link to attribution chain
        if source_content_id in self.attribution_chains:
            # Avoid duplicate visitors in chain
            if visitor_id not in self.attribution_chains[source_content_id]["visitors"]:
                self.attribution_chains[source_content_id]["visitors"].append(
                    visitor_id
                )

            # Update content visitor count (only once per visitor)
            if source_content_id in self.content_store:
                visitor_count = len(
                    set(self.attribution_chains[source_content_id]["visitors"])
                )
                self.content_store[source_content_id]["total_visitors"] = visitor_count

        return {"attribution_linked": True, "source_content_id": source_content_id}

    def track_lead_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track lead qualification with attribution maintenance.

        Args:
            lead_data: Lead qualification information

        Returns:
            Dictionary with lead qualification and attribution status
        """
        visitor_id = lead_data["visitor_id"]

        # Store lead record
        self.leads_store[visitor_id] = {
            "visitor_id": visitor_id,
            "visitor_type": lead_data.get("visitor_type", "unknown"),
            "hiring_manager_probability": lead_data.get(
                "hiring_manager_probability", 0
            ),
            "company_name": lead_data.get("company_name", ""),
            "is_target_company": lead_data.get("is_target_company", False),
            "qualified_at": datetime.utcnow(),
        }

        # Find source content and update attribution chain
        source_content_id = self._find_visitor_source_content(visitor_id)
        attribution_chain_active = False

        if source_content_id:
            self.attribution_chains[source_content_id]["leads"].append(visitor_id)

            # Update content qualified leads count
            if source_content_id in self.content_store:
                self.content_store[source_content_id]["qualified_leads"] += 1

            attribution_chain_active = True

        qualified_lead = (
            lead_data.get("visitor_type") == "hiring_manager"
            and lead_data.get("hiring_manager_probability", 0) > 0.7
        )

        return {
            "qualified_lead": qualified_lead,
            "attribution_chain_active": attribution_chain_active,
        }

    def track_interview_stage(
        self, visitor_id: str, stage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track interview stage progression with attribution maintenance.

        Args:
            visitor_id: Visitor identifier
            stage_data: Interview stage information

        Returns:
            Dictionary with stage tracking and attribution status
        """
        # Initialize interview tracking for visitor if not exists
        if visitor_id not in self.interviews_store:
            self.interviews_store[visitor_id] = []

        # Add stage record
        stage_record = {
            "stage": stage_data["stage"],
            "timestamp": stage_data.get("timestamp", datetime.utcnow()),
            "status": stage_data.get("status", "completed"),
        }

        self.interviews_store[visitor_id].append(stage_record)

        # Check if attribution chain is maintained
        source_content_id = self._find_visitor_source_content(visitor_id)
        attribution_maintained = source_content_id is not None

        return {
            "success": True,
            "stage": stage_data["stage"],
            "attribution_maintained": attribution_maintained,
        }

    def track_job_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track job offer with revenue attribution.

        Args:
            offer_data: Job offer information including salary and company

        Returns:
            Dictionary with offer tracking and revenue attribution
        """
        visitor_id = offer_data["visitor_id"]

        # Store offer record
        self.offers_store[visitor_id] = {
            "visitor_id": visitor_id,
            "company_name": offer_data.get("company_name", ""),
            "position": offer_data.get("position", ""),
            "initial_offer_amount": offer_data.get("initial_offer_amount", 0),
            "offer_date": offer_data.get("offer_date", datetime.utcnow()),
            "offer_status": offer_data.get("offer_status", "received"),
        }

        # Find all content pieces that this visitor interacted with
        visitor_content_touchpoints = self._find_visitor_all_touchpoints(visitor_id)
        revenue_attributed = False
        source_content_id = None

        if visitor_content_touchpoints:
            revenue_amount = offer_data.get("initial_offer_amount", 0)

            # Use linear attribution model - distribute revenue equally across touchpoints
            attribution_per_content = revenue_amount / len(visitor_content_touchpoints)

            for content_id in visitor_content_touchpoints:
                # Add visitor to offers list for this content
                if visitor_id not in self.attribution_chains[content_id]["offers"]:
                    self.attribution_chains[content_id]["offers"].append(visitor_id)

                # Update content with job offer and attributed revenue
                if content_id in self.content_store:
                    # Count unique job offers for this content
                    unique_offers = len(
                        set(self.attribution_chains[content_id]["offers"])
                    )
                    self.content_store[content_id]["job_offers"] = unique_offers

                    # Add attributed revenue (not full revenue to avoid double counting)
                    self.content_store[content_id]["attributed_revenue"] = (
                        attribution_per_content
                    )

            revenue_attributed = True
            source_content_id = visitor_content_touchpoints[
                0
            ]  # Return first touchpoint

        return {
            "revenue_attributed": revenue_attributed,
            "source_content_id": source_content_id,
        }

    def get_complete_attribution_chain(self, content_id: str) -> Dict[str, Any]:
        """
        Get complete attribution chain analysis for content piece.

        Args:
            content_id: Content identifier to analyze

        Returns:
            Complete attribution analysis with ROI calculation
        """
        if content_id not in self.content_store:
            return {}

        content_data = self.content_store[content_id]

        # Get attributed revenue (for multi-touchpoint scenarios)
        attributed_revenue = content_data.get(
            "attributed_revenue", content_data.get("revenue_amount", 0)
        )

        # Calculate ROI based on attributed revenue
        cost = content_data["creation_cost"]
        roi_percentage = 0

        if cost > 0:
            roi_percentage = ((attributed_revenue - cost) / cost) * 100

        # Calculate attribution confidence (simplified)
        attribution_confidence = (
            0.95  # High confidence for direct single-source attribution
        )

        return {
            "content_id": content_id,
            "platform": content_data["platform"],
            "total_visitors": content_data["total_visitors"],
            "qualified_leads": content_data["qualified_leads"],
            "job_offers": content_data["job_offers"],
            "revenue_amount": content_data.get(
                "revenue_amount", 0
            ),  # Total revenue if single-source
            "attributed_revenue": attributed_revenue,  # Attributed revenue for multi-touchpoint
            "content_creation_cost": cost,
            "roi_percentage": roi_percentage,
            "attribution_confidence": attribution_confidence,
        }

    def _find_visitor_source_content(self, visitor_id: str) -> Optional[str]:
        """Find the source content ID for a visitor"""
        for traffic_key, traffic_data in self.traffic_store.items():
            if traffic_data["visitor_id"] == visitor_id:
                return traffic_data["source_content_id"]
        return None

    def _find_visitor_all_touchpoints(self, visitor_id: str) -> List[str]:
        """Find all content pieces that a visitor interacted with"""
        touchpoints = []
        for traffic_key, traffic_data in self.traffic_store.items():
            if traffic_data["visitor_id"] == visitor_id:
                content_id = traffic_data["source_content_id"]
                if content_id not in touchpoints:
                    touchpoints.append(content_id)
        return touchpoints

    def analyze_platform_roi(
        self, platforms: List[str], date_range: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze ROI across platforms to compare effectiveness.

        Args:
            platforms: List of platform names to analyze
            date_range: Date range for analysis with start_date and end_date

        Returns:
            Dictionary with platform-specific ROI metrics
        """
        platform_results = {}

        for platform in platforms:
            # Get all content for this platform
            platform_content = [
                (content_id, content_data)
                for content_id, content_data in self.content_store.items()
                if content_data["platform"] == platform
            ]

            # Calculate platform metrics
            total_content_pieces = len(platform_content)
            total_visitors = sum(
                content_data["total_visitors"] for _, content_data in platform_content
            )
            qualified_leads = sum(
                content_data["qualified_leads"] for _, content_data in platform_content
            )
            job_offers = sum(
                content_data["job_offers"] for _, content_data in platform_content
            )

            # Calculate revenue (handle both single and multi-touchpoint scenarios)
            total_revenue = 0
            content_creation_cost = 0
            offer_amounts = []

            for content_id, content_data in platform_content:
                # Use attributed revenue if available, otherwise full revenue
                content_revenue = content_data.get(
                    "attributed_revenue", content_data.get("revenue_amount", 0)
                )
                total_revenue += content_revenue
                content_creation_cost += content_data.get("creation_cost", 0)

                # Collect offer amounts for average calculation
                for visitor_id in self.attribution_chains.get(content_id, {}).get(
                    "offers", []
                ):
                    if visitor_id in self.offers_store:
                        offer_amounts.append(
                            self.offers_store[visitor_id]["initial_offer_amount"]
                        )

            # Calculate derived metrics
            roi_percentage = 0
            if content_creation_cost > 0:
                roi_percentage = (
                    (total_revenue - content_creation_cost) / content_creation_cost
                ) * 100

            cost_per_lead = (
                content_creation_cost / qualified_leads if qualified_leads > 0 else 0
            )
            cost_per_offer = content_creation_cost / job_offers if job_offers > 0 else 0
            average_offer_amount = (
                sum(offer_amounts) / len(offer_amounts) if offer_amounts else 0
            )

            conversion_rate_traffic_to_lead = (
                qualified_leads / total_visitors if total_visitors > 0 else 0
            )
            conversion_rate_lead_to_offer = (
                job_offers / qualified_leads if qualified_leads > 0 else 0
            )

            platform_results[platform] = {
                "total_content_pieces": total_content_pieces,
                "total_visitors": total_visitors,
                "qualified_leads": qualified_leads,
                "job_offers": job_offers,
                "total_revenue": total_revenue,
                "content_creation_cost": content_creation_cost,
                "roi_percentage": roi_percentage,
                "cost_per_lead": cost_per_lead,
                "cost_per_offer": cost_per_offer,
                "average_offer_amount": average_offer_amount,
                "conversion_rate_traffic_to_lead": conversion_rate_traffic_to_lead,
                "conversion_rate_lead_to_offer": conversion_rate_lead_to_offer,
            }

        return platform_results

    def get_platform_effectiveness_ranking(
        self, metric: str = "revenue_per_content_piece"
    ) -> List[Dict[str, Any]]:
        """
        Rank platforms by effectiveness metric.

        Args:
            metric: Metric to rank by (e.g., 'revenue_per_content_piece', 'roi_percentage')

        Returns:
            List of platforms ranked by effectiveness
        """
        # Get all platforms from content store
        platforms = set(
            content_data["platform"] for content_data in self.content_store.values()
        )

        platform_rankings = []

        for platform in platforms:
            # Get platform ROI data
            platform_roi = self.analyze_platform_roi([platform], {})
            platform_data = platform_roi.get(platform, {})

            # Calculate metric value
            metric_value = 0
            if metric == "revenue_per_content_piece":
                total_content = platform_data.get("total_content_pieces", 0)
                total_revenue = platform_data.get("total_revenue", 0)
                metric_value = total_revenue / total_content if total_content > 0 else 0
            elif metric == "roi_percentage":
                metric_value = platform_data.get("roi_percentage", 0)
            elif metric == "conversion_rate_lead_to_offer":
                metric_value = platform_data.get("conversion_rate_lead_to_offer", 0)

            platform_rankings.append(
                {
                    "platform": platform,
                    "metric_value": metric_value,
                    "rank": 0,  # Will be set after sorting
                }
            )

        # Sort by metric value (descending)
        platform_rankings.sort(key=lambda x: x["metric_value"], reverse=True)

        # Assign ranks
        for i, platform_data in enumerate(platform_rankings):
            platform_data["rank"] = i + 1

        return platform_rankings

    def get_interview_pipeline_analysis(self, visitor_id: str) -> Dict[str, Any]:
        """
        Get complete interview pipeline analysis for a visitor.

        Args:
            visitor_id: Visitor identifier to analyze

        Returns:
            Complete pipeline analysis with stages, durations, and conversion rates
        """
        if visitor_id not in self.interviews_store:
            return {}

        stages = self.interviews_store[visitor_id]

        if not stages:
            return {}

        # Sort stages by timestamp
        sorted_stages = sorted(stages, key=lambda x: x["timestamp"])

        # Calculate pipeline metrics
        total_stages = len(sorted_stages)
        current_stage = sorted_stages[-1]["stage"]

        # Calculate pipeline completion rate (simplified)
        expected_stages = [
            "lead_generated",
            "initial_contact",
            "phone_screen_scheduled",
            "phone_screen_completed",
            "technical_interview_scheduled",
            "technical_interview_completed",
            "final_interview_scheduled",
            "final_interview_completed",
            "offer_received",
            "offer_accepted",
        ]

        completed_stage_names = [stage["stage"] for stage in sorted_stages]
        pipeline_completion_rate = len(completed_stage_names) / len(expected_stages)

        # Calculate total duration
        start_time = sorted_stages[0]["timestamp"]
        end_time = sorted_stages[-1]["timestamp"]
        total_duration = (end_time - start_time).days

        # Calculate stage durations
        stage_durations = {}
        for i in range(1, len(sorted_stages)):
            prev_stage = sorted_stages[i - 1]
            curr_stage = sorted_stages[i]
            duration = (curr_stage["timestamp"] - prev_stage["timestamp"]).days
            stage_durations[f"{prev_stage['stage']}_to_{curr_stage['stage']}"] = (
                duration
            )

        # Simple conversion rates (would be more complex with real data)
        conversion_rates_by_stage = {}
        for i, expected_stage in enumerate(expected_stages):
            if expected_stage in completed_stage_names:
                # Simplified: if stage exists, conversion rate is 100% from previous
                conversion_rates_by_stage[expected_stage] = 1.0
            else:
                conversion_rates_by_stage[expected_stage] = 0.0

        return {
            "total_stages": total_stages,
            "current_stage": current_stage,
            "pipeline_completion_rate": pipeline_completion_rate,
            "total_pipeline_duration_days": total_duration,
            "stage_durations": stage_durations,
            "conversion_rates_by_stage": conversion_rates_by_stage,
        }

    def calculate_pipeline_conversion_rates(self) -> Dict[str, float]:
        """
        Calculate conversion rates across all leads in the pipeline.

        Returns:
            Dictionary with conversion rates between each stage
        """
        # Collect all stages across all visitors
        stage_counts = {}

        for visitor_id, stages in self.interviews_store.items():
            completed_stages = set(stage["stage"] for stage in stages)

            # Count how many leads reached each stage
            for stage in completed_stages:
                if stage not in stage_counts:
                    stage_counts[stage] = 0
                stage_counts[stage] += 1

        # Calculate conversion rates between key stages
        conversion_rates = {}

        # Lead generated to phone screen
        lead_generated_count = stage_counts.get("lead_generated", 0)
        phone_screen_count = stage_counts.get("phone_screen_completed", 0)

        if lead_generated_count > 0:
            conversion_rates["lead_generated_to_phone_screen"] = (
                phone_screen_count / lead_generated_count
            )
        else:
            conversion_rates["lead_generated_to_phone_screen"] = 0.0

        # Phone screen to technical interview
        technical_interview_count = stage_counts.get("technical_interview_completed", 0)

        if phone_screen_count > 0:
            conversion_rates["phone_screen_to_technical_interview"] = (
                technical_interview_count / phone_screen_count
            )
        else:
            conversion_rates["phone_screen_to_technical_interview"] = 0.0

        # Technical interview to offer
        offer_received_count = stage_counts.get("offer_received", 0)

        if technical_interview_count > 0:
            conversion_rates["technical_interview_to_offer"] = (
                offer_received_count / technical_interview_count
            )
        else:
            conversion_rates["technical_interview_to_offer"] = 0.0

        # Offer to acceptance
        offer_accepted_count = stage_counts.get("offer_accepted", 0)

        if offer_received_count > 0:
            conversion_rates["offer_to_acceptance"] = (
                offer_accepted_count / offer_received_count
            )
        else:
            conversion_rates["offer_to_acceptance"] = 0.0

        return conversion_rates

    def track_salary_offer(
        self, visitor_id: str, offer_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track salary offer details for negotiation analysis.

        Args:
            visitor_id: Visitor identifier
            offer_details: Salary offer details including compensation breakdown

        Returns:
            Dictionary with offer tracking confirmation
        """
        # Initialize salary tracking for visitor if not exists
        if not hasattr(self, "salary_offers_store"):
            self.salary_offers_store = {}

        if visitor_id not in self.salary_offers_store:
            self.salary_offers_store[visitor_id] = []

        # Store offer record
        offer_record = {
            "offer_type": offer_details.get("offer_type", "initial"),
            "company_name": offer_details.get("company_name", ""),
            "position": offer_details.get("position", ""),
            "base_salary": offer_details.get("base_salary", 0),
            "equity_value": offer_details.get("equity_value", 0),
            "bonus": offer_details.get("bonus", 0),
            "total_compensation": offer_details.get("total_compensation", 0),
            "offer_date": offer_details.get("offer_date", datetime.utcnow()),
            "acceptance_status": offer_details.get("acceptance_status", "pending"),
        }

        self.salary_offers_store[visitor_id].append(offer_record)

        # Determine negotiation status
        offers = self.salary_offers_store[visitor_id]
        if len(offers) == 1 and offer_details.get("offer_type") == "initial":
            negotiation_status = "pending"
        elif offer_details.get("acceptance_status") == "accepted":
            negotiation_status = "completed"
        else:
            negotiation_status = "in_progress"

        return {"offer_tracked": True, "negotiation_status": negotiation_status}

    def track_salary_negotiation(
        self, visitor_id: str, negotiation_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track salary negotiation attempts and counter offers.

        Args:
            visitor_id: Visitor identifier
            negotiation_details: Negotiation details including requested amounts

        Returns:
            Dictionary with negotiation tracking confirmation
        """
        # Initialize negotiation tracking if not exists
        if not hasattr(self, "salary_negotiations_store"):
            self.salary_negotiations_store = {}

        if visitor_id not in self.salary_negotiations_store:
            self.salary_negotiations_store[visitor_id] = []

        # Store negotiation record
        negotiation_record = {
            "negotiation_type": negotiation_details.get(
                "negotiation_type", "counter_offer"
            ),
            "requested_base_salary": negotiation_details.get(
                "requested_base_salary", 0
            ),
            "requested_equity_value": negotiation_details.get(
                "requested_equity_value", 0
            ),
            "requested_total_compensation": negotiation_details.get(
                "requested_total_compensation", 0
            ),
            "justification": negotiation_details.get("justification", ""),
            "negotiation_date": negotiation_details.get(
                "negotiation_date", datetime.utcnow()
            ),
        }

        self.salary_negotiations_store[visitor_id].append(negotiation_record)

        return {"negotiation_tracked": True}

    def get_salary_negotiation_analysis(self, visitor_id: str) -> Dict[str, Any]:
        """
        Get complete salary negotiation analysis for a visitor.

        Args:
            visitor_id: Visitor identifier to analyze

        Returns:
            Complete negotiation analysis with amounts and outcomes
        """
        if (
            not hasattr(self, "salary_offers_store")
            or visitor_id not in self.salary_offers_store
        ):
            return {}

        offers = self.salary_offers_store[visitor_id]
        if not offers:
            return {}

        # Find initial and final offers
        initial_offer = None
        final_offer = None

        for offer in offers:
            if offer["offer_type"] == "initial":
                initial_offer = offer
            elif (
                offer["offer_type"] == "final"
                or offer["acceptance_status"] == "accepted"
            ):
                final_offer = offer

        if not initial_offer:
            return {}

        # Use final offer if available, otherwise use initial offer
        comparison_offer = final_offer if final_offer else initial_offer

        initial_amount = initial_offer["total_compensation"]
        final_amount = comparison_offer["total_compensation"]

        # Calculate negotiation metrics
        negotiation_increase = final_amount - initial_amount
        negotiation_percentage = (
            (negotiation_increase / initial_amount * 100) if initial_amount > 0 else 0
        )
        negotiation_success = negotiation_increase > 0

        # Calculate days to completion
        initial_date = initial_offer["offer_date"]
        final_date = comparison_offer["offer_date"]
        days_to_completion = (final_date - initial_date).days if final_offer else 0

        return {
            "initial_offer": initial_amount,
            "final_offer": final_amount,
            "negotiation_increase": negotiation_increase,
            "negotiation_percentage": negotiation_percentage,
            "negotiation_success": negotiation_success,
            "days_to_completion": days_to_completion,
        }

    def get_salary_benchmark_analysis(self, position: str) -> Dict[str, Any]:
        """
        Get salary benchmark analysis for a specific position.

        Args:
            position: Job position to analyze (e.g., "Senior MLOps Engineer")

        Returns:
            Benchmark analysis with salary statistics
        """
        if not hasattr(self, "salary_offers_store"):
            return {}

        # Collect all offers for the specified position
        position_offers = []

        for visitor_id, offers in self.salary_offers_store.items():
            for offer in offers:
                if (
                    offer["position"] == position
                    and offer["acceptance_status"] == "accepted"
                ):
                    position_offers.append(offer["total_compensation"])

        if not position_offers:
            return {"position": position, "total_offers": 0}

        # Calculate statistics
        total_offers = len(position_offers)
        average_compensation = sum(position_offers) / total_offers
        median_compensation = sorted(position_offers)[total_offers // 2]
        min_compensation = min(position_offers)
        max_compensation = max(position_offers)

        # Calculate compensation range (25th to 75th percentile)
        sorted_offers = sorted(position_offers)
        q1_index = total_offers // 4
        q3_index = 3 * total_offers // 4
        compensation_range = {
            "q1": sorted_offers[q1_index]
            if q1_index < total_offers
            else min_compensation,
            "q3": sorted_offers[q3_index]
            if q3_index < total_offers
            else max_compensation,
        }

        return {
            "position": position,
            "total_offers": total_offers,
            "average_compensation": round(average_compensation),
            "median_compensation": median_compensation,
            "min_compensation": min_compensation,
            "max_compensation": max_compensation,
            "compensation_range": compensation_range,
        }
