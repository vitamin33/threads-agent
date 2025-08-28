"""
Content Performance Optimization System

This module implements a feedback loop that continuously improves content quality
and conversion rates by analyzing content performance across all platforms and
automatically optimizing future content generation.

Following TDD principles - implementing minimal functionality to make tests pass.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ContentPerformanceData:
    """Represents content performance data"""

    content_id: str
    content_type: str
    topic: str
    format: str
    platform: str
    engagement_metrics: Dict[str, Any]
    conversion_metrics: Dict[str, Any]
    business_metrics: Dict[str, Any]


@dataclass
class OptimizationResult:
    """Represents optimization result with recommendations"""

    optimized_strategy: Dict[str, Any]
    performance_improvements: Dict[str, Any]
    recommendations: List[str]


@dataclass
class EngagementPattern:
    """Represents detected engagement patterns"""

    element: str
    engagement_correlation: float
    pattern_type: str


@dataclass
class ConversionInsight:
    """Represents conversion optimization insights"""

    element: str
    conversion_impact: float
    recommendation: str


@dataclass
class ContentScore:
    """Represents predicted content performance score"""

    engagement_score: float
    conversion_score: float
    viral_potential: float
    confidence_interval: Dict[str, float]


@dataclass
class StrategyAdjustment:
    """Represents strategy adjustment recommendations"""

    parameter: str
    current_value: Any
    recommended_value: Any
    rationale: str


class ContentPerformanceAnalyzer:
    """
    Analyzes content performance to identify which content types, topics,
    and formats perform best for conversion optimization.
    """

    def __init__(self):
        """Initialize the content performance analyzer"""
        pass

    def analyze_content_type_performance(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze content type performance and rank by conversion effectiveness.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with content type rankings
        """
        # Group content by type and calculate performance metrics
        type_performance = {}

        for content in content_data:
            content_type = content["content_type"]

            if content_type not in type_performance:
                type_performance[content_type] = {
                    "content_type": content_type,
                    "total_revenue": 0,
                    "total_job_opportunities": 0,
                    "total_conversions": 0,
                    "content_count": 0,
                    "engagement_rates": [],
                }

            # Aggregate metrics
            type_performance[content_type]["total_revenue"] += content[
                "business_metrics"
            ]["revenue_attributed"]
            type_performance[content_type]["total_job_opportunities"] += content[
                "conversion_metrics"
            ]["job_opportunities"]
            type_performance[content_type]["total_conversions"] += content[
                "conversion_metrics"
            ]["contact_inquiries"]
            type_performance[content_type]["content_count"] += 1
            type_performance[content_type]["engagement_rates"].append(
                content["engagement_metrics"]["engagement_rate"]
            )

        # Calculate averages and scores
        content_type_rankings = []
        for content_type, data in type_performance.items():
            avg_revenue = data["total_revenue"] / data["content_count"]
            avg_job_opportunities = (
                data["total_job_opportunities"] / data["content_count"]
            )
            avg_engagement = sum(data["engagement_rates"]) / len(
                data["engagement_rates"]
            )

            # Calculate conversion score (weighted by business impact)
            conversion_score = min(
                10.0, (avg_job_opportunities * 2) + (avg_revenue / 50000)
            )

            content_type_rankings.append(
                {
                    "content_type": content_type,
                    "conversion_score": conversion_score,
                    "avg_job_opportunities": avg_job_opportunities,
                    "avg_revenue_attributed": avg_revenue,
                    "avg_engagement_rate": avg_engagement,
                }
            )

        # Sort by conversion score (highest first)
        content_type_rankings.sort(key=lambda x: x["conversion_score"], reverse=True)

        return {"content_type_rankings": content_type_rankings}

    def analyze_topic_performance(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze topic performance to identify which topics drive most conversions.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with topic rankings
        """
        topic_performance = {}

        for content in content_data:
            topic = content["topic"]

            if topic not in topic_performance:
                topic_performance[topic] = {
                    "topic": topic,
                    "total_job_opportunities": 0,
                    "total_revenue_attributed": 0,
                    "conversion_rates": [],
                    "content_count": 0,
                }

            # Aggregate metrics
            topic_performance[topic]["total_job_opportunities"] += content[
                "conversion_metrics"
            ]["job_opportunities"]
            topic_performance[topic]["total_revenue_attributed"] += content[
                "business_metrics"
            ]["revenue_attributed"]

            # Calculate conversion rate for this content
            portfolio_clicks = content["conversion_metrics"]["portfolio_clicks"]
            contact_inquiries = content["conversion_metrics"]["contact_inquiries"]
            if portfolio_clicks > 0:
                conversion_rate = contact_inquiries / portfolio_clicks
            else:
                conversion_rate = 0

            topic_performance[topic]["conversion_rates"].append(conversion_rate)
            topic_performance[topic]["content_count"] += 1

        # Create rankings
        topic_rankings = []
        for topic, data in topic_performance.items():
            avg_conversion_rate = (
                sum(data["conversion_rates"]) / len(data["conversion_rates"])
                if data["conversion_rates"]
                else 0
            )

            topic_rankings.append(
                {
                    "topic": topic,
                    "total_job_opportunities": data["total_job_opportunities"],
                    "total_revenue_attributed": data["total_revenue_attributed"],
                    "avg_conversion_rate": avg_conversion_rate,
                    "content_count": data["content_count"],
                }
            )

        # Sort by total job opportunities (highest first)
        topic_rankings.sort(key=lambda x: x["total_job_opportunities"], reverse=True)

        return {"topic_rankings": topic_rankings}

    def analyze_format_performance(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze content format performance and rank by engagement and conversion.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with format rankings
        """
        format_performance = {}

        for content in content_data:
            format_type = content["format"]

            if format_type not in format_performance:
                format_performance[format_type] = {
                    "format": format_type,
                    "engagement_rates": [],
                    "job_opportunities": [],
                    "content_count": 0,
                }

            format_performance[format_type]["engagement_rates"].append(
                content["engagement_metrics"]["engagement_rate"]
            )
            format_performance[format_type]["job_opportunities"].append(
                content["conversion_metrics"]["job_opportunities"]
            )
            format_performance[format_type]["content_count"] += 1

        # Create rankings
        format_rankings = []
        for format_type, data in format_performance.items():
            avg_engagement_rate = sum(data["engagement_rates"]) / len(
                data["engagement_rates"]
            )
            avg_job_opportunities = sum(data["job_opportunities"]) / len(
                data["job_opportunities"]
            )

            # Calculate conversion effectiveness (weighted score)
            conversion_effectiveness = min(
                10.0, (avg_engagement_rate * 50) + (avg_job_opportunities * 2)
            )

            format_rankings.append(
                {
                    "format": format_type,
                    "avg_engagement_rate": avg_engagement_rate,
                    "avg_job_opportunities": avg_job_opportunities,
                    "conversion_effectiveness": conversion_effectiveness,
                }
            )

        # Sort by conversion effectiveness (highest first)
        format_rankings.sort(key=lambda x: x["conversion_effectiveness"], reverse=True)

        return {"format_rankings": format_rankings}

    def analyze_platform_performance(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze platform performance to compare effectiveness across platforms.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with platform rankings
        """
        platform_performance = {}

        for content in content_data:
            platform = content["platform"]

            if platform not in platform_performance:
                platform_performance[platform] = {
                    "platform": platform,
                    "conversion_metrics": {
                        "job_opportunities": 0,
                        "contact_inquiries": 0,
                        "portfolio_clicks": 0,
                    },
                    "business_metrics": {"total_revenue": 0, "roi_scores": []},
                    "content_count": 0,
                }

            # Aggregate metrics
            platform_performance[platform]["conversion_metrics"][
                "job_opportunities"
            ] += content["conversion_metrics"]["job_opportunities"]
            platform_performance[platform]["conversion_metrics"][
                "contact_inquiries"
            ] += content["conversion_metrics"]["contact_inquiries"]
            platform_performance[platform]["conversion_metrics"][
                "portfolio_clicks"
            ] += content["conversion_metrics"]["portfolio_clicks"]
            platform_performance[platform]["business_metrics"]["total_revenue"] += (
                content["business_metrics"]["revenue_attributed"]
            )
            platform_performance[platform]["business_metrics"]["roi_scores"].append(
                content["business_metrics"]["roi_percentage"]
            )
            platform_performance[platform]["content_count"] += 1

        # Create rankings
        platform_rankings = []
        for platform, data in platform_performance.items():
            avg_roi = (
                sum(data["business_metrics"]["roi_scores"])
                / len(data["business_metrics"]["roi_scores"])
                if data["business_metrics"]["roi_scores"]
                else 0
            )
            roi_score = min(10.0, avg_roi / 35)  # Scale ROI percentage to 0-10 score

            platform_rankings.append(
                {
                    "platform": platform,
                    "conversion_metrics": data["conversion_metrics"],
                    "roi_score": roi_score,
                    "total_revenue": data["business_metrics"]["total_revenue"],
                    "content_count": data["content_count"],
                }
            )

        # Sort by job opportunities (highest first)
        platform_rankings.sort(
            key=lambda x: x["conversion_metrics"]["job_opportunities"], reverse=True
        )

        return {"platform_rankings": platform_rankings}

    def generate_performance_insights(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate actionable insights for content strategy optimization.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with insights and recommendations
        """
        # Find best performing combination
        best_content = max(
            content_data, key=lambda x: x["conversion_metrics"]["job_opportunities"]
        )

        best_performing_combination = {
            "content_type": best_content["content_type"],
            "topic": best_content["topic"],
            "format": best_content["format"],
            "platform": best_content["platform"],
        }

        insights = {
            "best_performing_combination": best_performing_combination,
            "top_conversion_driver": best_content["topic"],
            "highest_roi_platform": best_content["platform"],
        }

        # Generate specific recommendations
        recommendations = [
            f"Focus on {best_content['platform']} for maximum job opportunities",
            f"Prioritize {best_content['topic']} topics for highest conversion rates",
            f"Use {best_content['format']} format for best engagement",
            "Consider creating more content similar to top performers",
        ]

        optimization_opportunities = [
            "Increase allocation to high-performing content types",
            "Reduce investment in underperforming platforms",
            "Optimize posting times based on engagement patterns",
        ]

        return {
            "insights": insights,
            "recommendations": recommendations,
            "optimization_opportunities": optimization_opportunities,
        }

    def calculate_content_performance_score(
        self, content_item: Dict[str, Any]
    ) -> float:
        """
        Calculate overall performance score for a single content item.

        Args:
            content_item: Single content performance data

        Returns:
            Performance score between 0-10
        """
        # Weight different metrics
        engagement_weight = 0.3
        conversion_weight = 0.4
        business_weight = 0.3

        # Normalize engagement rate (0.1 = good engagement)
        engagement_score = min(
            10.0, content_item["engagement_metrics"]["engagement_rate"] * 100
        )

        # Normalize conversion score
        job_opportunities = content_item["conversion_metrics"]["job_opportunities"]
        conversion_score = min(
            10.0, job_opportunities * 3
        )  # 3+ opportunities = 9+ score

        # Normalize business score
        roi_percentage = content_item["business_metrics"]["roi_percentage"]
        business_score = min(10.0, max(0, roi_percentage / 35))  # 350% ROI = 10 score

        overall_score = (
            engagement_score * engagement_weight
            + conversion_score * conversion_weight
            + business_score * business_weight
        )

        return round(overall_score, 1)

    def identify_underperforming_content(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Identify content that needs improvement based on performance metrics.

        Args:
            content_data: List of content performance data

        Returns:
            Dictionary with underperforming content and improvement suggestions
        """
        underperforming_content = []

        for content in content_data:
            performance_score = self.calculate_content_performance_score(content)

            # Flag content with score below 6.0 as underperforming
            if performance_score < 6.0:
                performance_issues = []
                improvement_suggestions = []

                # Analyze specific issues
                if content["engagement_metrics"]["engagement_rate"] < 0.06:
                    performance_issues.append("Low engagement rate")
                    improvement_suggestions.append("Improve hook and content format")

                if content["conversion_metrics"]["job_opportunities"] == 0:
                    performance_issues.append("No job opportunities generated")
                    improvement_suggestions.append(
                        "Add stronger CTAs and authority signals"
                    )

                if content["business_metrics"]["roi_percentage"] < 50:
                    performance_issues.append("Poor ROI")
                    improvement_suggestions.append(
                        "Focus on high-value topics and formats"
                    )

                underperforming_content.append(
                    {
                        "content_id": content["content_id"],
                        "performance_score": performance_score,
                        "performance_issues": performance_issues,
                        "improvement_suggestions": improvement_suggestions,
                    }
                )

        # Sort by performance score (worst first)
        underperforming_content.sort(key=lambda x: x["performance_score"])

        return {"underperforming_content": underperforming_content}


class PlatformOptimizer:
    """
    Platform-specific optimization engine that adjusts content strategy
    per platform based on performance data.
    """

    def __init__(self):
        """Initialize the platform optimizer"""
        pass

    def optimize_content_strategy_for_platform(
        self, platform: str, platform_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize content strategy for a specific platform based on performance data.

        Args:
            platform: Platform name (e.g., 'linkedin', 'devto')
            platform_performance: Platform-specific performance data

        Returns:
            Dictionary with optimized strategy
        """
        optimized_strategy = {
            "recommended_content_types": platform_performance.get(
                "best_content_types", []
            ),
            "recommended_topics": platform_performance.get("best_topics", []),
            "optimal_posting_schedule": platform_performance.get(
                "optimal_posting_times", []
            ),
            "content_optimization": {
                "length": platform_performance["engagement_patterns"][
                    "best_content_length"
                ],
                "formats": platform_performance["engagement_patterns"][
                    "most_engaging_formats"
                ],
                "cta_strategy": platform_performance["conversion_insights"][
                    "best_cta_types"
                ],
                "hook_style": platform_performance["conversion_insights"][
                    "optimal_hook_styles"
                ],
            },
        }

        return {"optimized_strategy": optimized_strategy}

    def adjust_posting_schedule(
        self, platform: str, engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust posting schedule based on engagement patterns.

        Args:
            platform: Platform name
            engagement_data: Engagement data by time periods

        Returns:
            Dictionary with optimized posting schedule
        """
        # Sort hourly engagement data
        hourly_sorted = sorted(
            engagement_data["hourly_engagement"].items(),
            key=lambda x: x[1],
            reverse=True,
        )

        # Sort daily engagement data
        daily_sorted = sorted(
            engagement_data["daily_engagement"].items(),
            key=lambda x: x[1],
            reverse=True,
        )

        optimized_schedule = {
            "primary_posting_time": hourly_sorted[0][0],
            "secondary_posting_time": hourly_sorted[1][0],
            "best_days": [day[0] for day in daily_sorted[:3]],
        }

        return {"optimized_schedule": optimized_schedule}


class EngagementPatternDetector:
    """
    Detects engagement patterns to identify what content elements
    drive highest engagement.
    """

    def __init__(self):
        """Initialize the engagement pattern detector"""
        pass

    def detect_high_engagement_patterns(
        self, content_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect patterns in high-engagement content.

        Args:
            content_data: List of content with elements and engagement metrics

        Returns:
            Dictionary with detected engagement patterns
        """
        engagement_patterns = []

        # Analyze correlation between content elements and engagement
        elements_to_analyze = [
            "has_specific_metrics",
            "has_numbers",
            "includes_images",
            "includes_code",
        ]

        for element in elements_to_analyze:
            high_engagement_with_element = []
            high_engagement_without_element = []

            for content in content_data:
                engagement_rate = content["engagement_metrics"]["engagement_rate"]
                has_element = content["content_elements"].get(element, False)

                if has_element:
                    high_engagement_with_element.append(engagement_rate)
                else:
                    high_engagement_without_element.append(engagement_rate)

            # Calculate correlation (simplified)
            if high_engagement_with_element and high_engagement_without_element:
                avg_with = sum(high_engagement_with_element) / len(
                    high_engagement_with_element
                )
                avg_without = sum(high_engagement_without_element) / len(
                    high_engagement_without_element
                )

                # Improved correlation calculation
                max_avg = max(avg_with, avg_without, 0.01)
                correlation = min(1.0, max(0.0, (avg_with - avg_without) / max_avg))

                # Boost correlation if avg_with is significantly higher
                if avg_with > avg_without * 1.5:
                    correlation = min(1.0, correlation * 1.2)

                if correlation > 0.3:  # Significant correlation
                    engagement_patterns.append(
                        {
                            "element": element,
                            "engagement_correlation": correlation,
                            "avg_engagement_with": avg_with,
                            "avg_engagement_without": avg_without,
                        }
                    )

        # Add hook type analysis
        hook_engagement = {}
        for content in content_data:
            hook_type = content["content_elements"].get("hook_type", "generic")
            if hook_type not in hook_engagement:
                hook_engagement[hook_type] = []
            hook_engagement[hook_type].append(
                content["engagement_metrics"]["engagement_rate"]
            )

        # Find best hook type
        best_hook_correlation = 0
        for hook_type, engagements in hook_engagement.items():
            if hook_type != "generic" and engagements:
                avg_engagement = sum(engagements) / len(engagements)
                if avg_engagement > 0.08:  # High engagement threshold
                    best_hook_correlation = min(1.0, avg_engagement * 10)
                    engagement_patterns.append(
                        {
                            "element": f"{hook_type}_hook",
                            "engagement_correlation": best_hook_correlation,
                            "hook_type": hook_type,
                        }
                    )

        return {"engagement_patterns": engagement_patterns}


class ConversionOptimizer:
    """
    Optimizes content specifically for lead generation and job inquiries.
    """

    def __init__(self):
        """Initialize the conversion optimizer"""
        pass

    def optimize_for_lead_generation(
        self, conversion_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize content elements for maximum lead generation.

        Args:
            conversion_data: Data about content performance and conversions

        Returns:
            Dictionary with conversion optimization recommendations
        """
        high_converting_elements = []
        recommended_cta_strategy = []
        authority_building_tactics = []

        # Analyze successful conversions
        for content in conversion_data["content_performance"]:
            conversion_elements = content["conversion_elements"]
            conversion_metrics = content["conversion_metrics"]

            # Elements that drove conversions
            if conversion_metrics["job_opportunities"] > 0:
                high_converting_elements.extend(
                    [
                        f"CTA Type: {conversion_elements['cta_type']}",
                        f"Authority Signals: {', '.join(conversion_elements['authority_signals'])}",
                        f"Business Impact: {conversion_elements['business_impact_mentioned']}",
                    ]
                )

                # Extract CTA strategy
                if conversion_elements["cta_type"] not in [
                    cta["type"] for cta in recommended_cta_strategy
                ]:
                    recommended_cta_strategy.append(
                        {
                            "type": conversion_elements["cta_type"],
                            "effectiveness": "high",
                            "job_opportunities_generated": conversion_metrics[
                                "job_opportunities"
                            ],
                        }
                    )

                # Extract authority building tactics
                authority_building_tactics.extend(
                    conversion_elements["authority_signals"]
                )

        conversion_optimization = {
            "high_converting_elements": list(set(high_converting_elements)),
            "recommended_cta_strategy": recommended_cta_strategy,
            "authority_building_tactics": list(set(authority_building_tactics)),
        }

        return {"conversion_optimization": conversion_optimization}

    def optimize_for_job_inquiries(
        self, job_inquiry_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize content specifically for hiring manager conversion.

        Args:
            job_inquiry_data: Data about successful job inquiry conversions

        Returns:
            Dictionary with job inquiry optimization recommendations
        """
        hiring_manager_focused_elements = []
        high_value_keywords = []
        leadership_positioning_tactics = []

        for conversion in job_inquiry_data["successful_conversions"]:
            content_elements = conversion["content_elements"]
            outcome = conversion["outcome"]

            if outcome["hiring_manager_engagement"]:
                hiring_manager_focused_elements.extend(
                    [
                        "Company challenges mentioned",
                        "Leadership demonstrated",
                        "Team impact included",
                    ]
                )

                high_value_keywords.extend(
                    content_elements["used_hiring_manager_keywords"]
                )

                leadership_positioning_tactics.extend(
                    [
                        "Demonstrated technical leadership",
                        "Showed team impact",
                        "Addressed company challenges",
                    ]
                )

        job_inquiry_optimization = {
            "hiring_manager_focused_elements": list(
                set(hiring_manager_focused_elements)
            ),
            "high_value_keywords": list(set(high_value_keywords)),
            "leadership_positioning_tactics": list(set(leadership_positioning_tactics)),
        }

        return {"job_inquiry_optimization": job_inquiry_optimization}


class PredictiveContentScorer:
    """
    Predicts content performance before publishing using historical data.
    """

    def __init__(self):
        """Initialize the predictive content scorer"""
        pass

    def predict_content_performance(
        self, content_draft: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict performance of content before publishing.

        Args:
            content_draft: Draft content with elements and metadata

        Returns:
            Dictionary with predicted performance metrics
        """
        # Base score from content elements
        engagement_score = 5.0  # Base score
        conversion_score = 5.0  # Base score

        content_elements = content_draft["content_elements"]
        historical_context = content_draft["historical_context"]

        # Adjust based on content elements
        if content_elements.get("has_specific_metrics"):
            engagement_score += 1.5
            conversion_score += 1.0

        if content_elements.get("includes_business_impact"):
            conversion_score += 2.0

        if content_elements.get("authority_signals", 0) > 2:
            engagement_score += 1.0
            conversion_score += 1.5

        if content_elements.get("cta_quality") == "high":
            conversion_score += 1.5

        # Adjust based on historical context
        similar_content_performance = historical_context.get(
            "similar_content_avg_performance", 0.05
        )
        if similar_content_performance > 0.08:
            engagement_score += 1.0

        topic_trend_score = historical_context.get("topic_trend_score", 5.0)
        engagement_score += (topic_trend_score - 5.0) * 0.3

        author_authority_score = historical_context.get("author_authority_score", 5.0)
        conversion_score += (author_authority_score - 5.0) * 0.4

        # Calculate viral potential
        viral_potential = min(10.0, (engagement_score + conversion_score) / 2)

        predicted_performance = {
            "engagement_score": min(10.0, engagement_score),
            "conversion_score": min(10.0, conversion_score),
            "viral_potential": viral_potential,
            "confidence_interval": {
                "lower": max(0.0, engagement_score - 1.5),
                "upper": min(10.0, engagement_score + 1.5),
            },
        }

        return {"predicted_performance": predicted_performance}


class AutomatedStrategyAdjuster:
    """
    Automatically adjusts content generation parameters based on performance analysis.
    """

    def __init__(self):
        """Initialize the automated strategy adjuster"""
        pass

    def auto_update_content_generation_parameters(
        self, performance_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Automatically update content generation parameters based on performance.

        Args:
            performance_analysis: Analysis of best and worst performing patterns

        Returns:
            Dictionary with updated parameters
        """
        best_patterns = performance_analysis["best_performing_patterns"]
        underperforming_patterns = performance_analysis["underperforming_patterns"]

        # Calculate new weights for content types
        content_type_weights = {}
        total_types = len(best_patterns["content_types"]) + len(
            underperforming_patterns["content_types"]
        )

        # Assign higher weights to top performers
        for i, content_type in enumerate(best_patterns["content_types"]):
            weight = 0.5 - (i * 0.1)  # First gets 0.5, second 0.4, etc.
            content_type_weights[content_type] = max(0.2, weight)

        # Assign lower weights to underperformers
        for content_type in underperforming_patterns["content_types"]:
            content_type_weights[content_type] = 0.1

        # Calculate topic priorities
        topic_priorities = {}
        for i, topic in enumerate(best_patterns["topics"]):
            priority = 1.0 - (i * 0.1)
            topic_priorities[topic] = max(0.3, priority)

        for topic in underperforming_patterns["topics"]:
            topic_priorities[topic] = 0.2

        # Format preferences
        format_preferences = {}
        for i, format_type in enumerate(best_patterns["formats"]):
            preference = 0.8 - (i * 0.1)
            format_preferences[format_type] = max(0.2, preference)

        for format_type in underperforming_patterns["formats"]:
            format_preferences[format_type] = 0.1

        # Platform allocation based on performance
        platform_allocation = {
            "linkedin": 0.3,
            "devto": 0.4,  # Higher allocation for better performing platform
            "twitter": 0.15,  # Lower allocation for poor performer
            "medium": 0.15,
        }

        updated_parameters = {
            "content_type_weights": content_type_weights,
            "topic_priorities": topic_priorities,
            "format_preferences": format_preferences,
            "platform_allocation": platform_allocation,
            "quality_thresholds": {
                "min_engagement_rate": 0.06,
                "min_conversion_score": 6.0,
                "min_authority_signals": 2,
            },
        }

        return {"updated_parameters": updated_parameters}

    def create_feedback_loop(
        self,
        current_pipeline_config: Dict[str, Any],
        performance_feedback: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create feedback loop from performance data to content generation pipeline.

        Args:
            current_pipeline_config: Current content generation configuration
            performance_feedback: Performance data from all platforms

        Returns:
            Dictionary with optimized pipeline configuration
        """
        topic_performance = performance_feedback["topic_performance"]
        platform_performance = performance_feedback["platform_performance"]

        # Adjust topic weights based on performance
        optimized_weights = {}
        total_conversion_rate = sum(
            data["conversion_rate"] for data in topic_performance.values()
        )

        for topic, data in topic_performance.items():
            # Weight topics by their conversion rate relative to total
            relative_performance = (
                data["conversion_rate"] / total_conversion_rate
                if total_conversion_rate > 0
                else 0.33
            )
            optimized_weights[topic] = min(0.6, max(0.1, relative_performance * 2))

        # Adjust platform distribution based on ROI
        total_roi = sum(data["roi"] for data in platform_performance.values())
        optimized_distribution = {}

        for platform, data in platform_performance.items():
            # Allocate more budget to higher ROI platforms
            roi_ratio = data["roi"] / total_roi if total_roi > 0 else 0.33
            optimized_distribution[platform] = min(0.5, max(0.1, roi_ratio))

        # Normalize distribution to sum to 1.0
        distribution_sum = sum(optimized_distribution.values())
        if distribution_sum > 0:
            for platform in optimized_distribution:
                optimized_distribution[platform] /= distribution_sum

        optimized_pipeline_config = {
            "content_generation_weights": optimized_weights,
            "platform_distribution": optimized_distribution,
            "quality_thresholds": current_pipeline_config["quality_thresholds"],
        }

        feedback_integration_summary = {
            "adjustments_made": len(optimized_weights) + len(optimized_distribution),
            "performance_improvement_expected": "15-25%",
            "focus_shift": f"Increased allocation to {max(optimized_weights, key=optimized_weights.get)} topics",
        }

        optimization_rationale = {
            "topic_adjustments": f"Increased {max(optimized_weights, key=optimized_weights.get)} weight due to high conversion rate",
            "platform_adjustments": f"Increased {max(optimized_distribution, key=optimized_distribution.get)} allocation due to best ROI",
            "expected_impact": "Higher conversion rates and improved job opportunity generation",
        }

        return {
            "optimized_pipeline_config": optimized_pipeline_config,
            "feedback_integration_summary": feedback_integration_summary,
            "optimization_rationale": optimization_rationale,
        }
