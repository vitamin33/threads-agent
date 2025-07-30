"""Enhanced business value calculator with agile KPIs and realistic estimates."""

import re
from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum


class ValueType(Enum):
    """Types of business value."""

    TIME_SAVINGS = "time_savings"
    COST_REDUCTION = "cost_reduction"
    REVENUE_INCREASE = "revenue_increase"
    RISK_MITIGATION = "risk_mitigation"
    PRODUCTIVITY_GAIN = "productivity_gain"
    QUALITY_IMPROVEMENT = "quality_improvement"
    TECHNICAL_DEBT_REDUCTION = "technical_debt_reduction"
    AUTOMATION = "automation"


@dataclass
class BusinessValueConfig:
    """Configuration for business value calculations."""

    # Hourly rates by role
    junior_dev_rate: float = 75.0
    mid_dev_rate: float = 100.0
    senior_dev_rate: float = 125.0
    tech_lead_rate: float = 150.0

    # Infrastructure costs
    server_cost_monthly: float = 500.0
    ci_cost_monthly: float = 200.0
    monitoring_cost_monthly: float = 150.0

    # Incident costs by severity
    critical_incident_cost: float = 25000.0
    major_incident_cost: float = 10000.0
    minor_incident_cost: float = 2500.0

    # Agile metrics
    story_point_hour_ratio: float = 8.0  # hours per story point
    defect_fix_cost: float = 1200.0  # average cost to fix a defect
    deployment_time_savings_value: float = 200.0  # per hour saved

    # Team sizes for scaling
    typical_team_size: int = 5

    # Confidence factors
    high_confidence: float = 0.9
    medium_confidence: float = 0.7
    low_confidence: float = 0.4


class AgileBusinessValueCalculator:
    """Enhanced business value calculator with agile KPIs."""

    def __init__(self, config: BusinessValueConfig = None):
        self.config = config or BusinessValueConfig()

    def extract_business_value(
        self, pr_description: str, pr_metrics: Dict = None
    ) -> Optional[Dict]:
        """Extract business value using multiple calculation methods."""
        pr_metrics = pr_metrics or {}

        # Try different extraction methods in priority order (complex calculations first)
        for method in [
            self._extract_time_savings,  # 1st - Most valuable and accurate
            self._extract_performance_improvements,  # 2nd - High business impact
            self._extract_automation_value,  # 3rd - Complex value calculations
            self._extract_quality_improvements,  # 4th - Measurable impact metrics
            self._extract_risk_mitigation,  # 5th - High-value risk scenarios
            self._extract_technical_debt_reduction,  # 6th - Long-term value
            self._extract_explicit_value,  # 7th - Simple dollar extraction (fallback)
            self._infer_from_pr_size,  # 8th - Last resort estimation
        ]:
            result = method(pr_description, pr_metrics)
            if result:
                return result

        return None

    def _extract_explicit_value(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract explicitly mentioned dollar amounts."""
        patterns = [
            r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?(year|yearly|annual|annually|month|monthly)?",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*dollars?\s*(?:per\s+)?(year|yearly|annual|annually|month|monthly)?",
            r"saves?\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:per\s+)?(year|yearly|annual|annually|month|monthly)?",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                amount = float(match.group(1).replace(",", ""))
                period = match.group(2) if len(match.groups()) > 1 else "yearly"

                # Normalize to yearly
                if period and "month" in period.lower():
                    amount *= 12

                return {
                    "total_value": int(amount),
                    "currency": "USD",
                    "period": "yearly",
                    "type": ValueType.COST_REDUCTION.value,
                    "confidence": self.config.high_confidence,
                    "method": "explicit_mention",
                    "source": match.group(0),
                }
        return None

    def _extract_time_savings(self, description: str, metrics: Dict) -> Optional[Dict]:
        """Extract time savings with role-based hourly rates."""
        patterns = [
            r"sav(?:es?|ing)\s+(\d+(?:\.\d+)?)\s+hours?\s*(?:per\s+)?(week|month|year|daily|sprint)?\s*(?:for\s+)?(senior|junior|lead|mid|developer|dev|engineer)s?\s*(?:developer|dev|engineer)s?",
            r"sav(?:es?|ing)\s+(\d+(?:\.\d+)?)\s+(?:(senior|junior|lead|mid|developer|dev|engineer)s?\s+)?hours?\s*(?:per\s+)?(week|month|year|daily|sprint)?",
            r"(?:reduces?|cut|eliminates?)\s+(\d+(?:\.\d+)?)\s+(?:(senior|junior|lead|mid|developer|dev|engineer)s?\s+)?hours?\s*(?:per\s+)?(week|month|year|daily|sprint)?",
            r"(\d+(?:\.\d+)?)\s+hours?\s*(?:per\s+)?(week|month|year|daily|sprint)?\s*(?:for\s+)?(senior|junior|lead|mid|developer|dev|engineer)s?\s*(?:developer|dev|engineer)s?",
            r"(\d+(?:\.\d+)?)\s+(?:(senior|junior|lead|mid|developer|dev|engineer)s?\s+)?hours?\s+(?:saved|reduction|less)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                hours = float(match.group(1))

                # Extract role and period from all groups
                groups = [g for g in match.groups() if g]
                role = "mid"  # default
                period = "week"  # default

                for group in groups[1:]:  # Skip first group (hours)
                    if group and group.lower() in [
                        "week",
                        "month",
                        "year",
                        "daily",
                        "sprint",
                    ]:
                        period = group.lower()
                    elif group and any(
                        r in group.lower()
                        for r in [
                            "senior",
                            "junior",
                            "lead",
                            "mid",
                            "developer",
                            "dev",
                            "engineer",
                        ]
                    ):
                        role = group.lower()

                # Determine hourly rate based on role
                if "senior" in role or "lead" in role:
                    hourly_rate = self.config.senior_dev_rate
                elif "junior" in role:
                    hourly_rate = self.config.junior_dev_rate
                else:
                    hourly_rate = self.config.mid_dev_rate

                # Convert to annual hours
                annual_hours = self._normalize_to_annual_hours(hours, period)

                # Scale by team size if it affects multiple developers
                team_multiplier = 1

                # Check for specific team size mentions
                team_size_match = re.search(
                    r"(\d+)[-\s]*(?:person|people|member|developer|engineer)s?\s+team",
                    description,
                    re.IGNORECASE,
                )
                if team_size_match:
                    team_multiplier = int(team_size_match.group(1))
                # Check for general team mentions
                elif re.search(
                    r"team|developers|engineers", description, re.IGNORECASE
                ):
                    team_multiplier = self.config.typical_team_size

                annual_hours *= team_multiplier

                return {
                    "total_value": int(annual_hours * hourly_rate),
                    "currency": "USD",
                    "period": "yearly",
                    "type": ValueType.TIME_SAVINGS.value,
                    "confidence": self.config.medium_confidence,
                    "method": "time_calculation",
                    "breakdown": {
                        "hours_saved_annually": annual_hours,
                        "hourly_rate": hourly_rate,
                        "role_assumed": role,
                        "team_multiplier": team_multiplier,
                        "base_hours_per_person": annual_hours // team_multiplier
                        if team_multiplier > 1
                        else annual_hours,
                    },
                }
        return None

    def _extract_performance_improvements(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract performance improvements with infrastructure cost models."""
        patterns = [
            r"(?:performance|response\s+time|latency|throughput).*?(?:improv|increas|reduc|optim).*?(\d+(?:\.\d+)?)%",
            r"(\d+(?:\.\d+)?)%.*?(?:faster|quicker|improvement|reduction).*?(?:performance|response|latency)",
            r"(?:reduc|decreas).*?(?:by\s+)?(\d+(?:\.\d+)?)%.*?(?:response\s+time|latency|load\s+time)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                percentage = float(match.group(1))

                # Calculate infrastructure savings based on performance improvement
                monthly_infra_cost = self.config.server_cost_monthly

                # Performance improvements can reduce infrastructure needs
                monthly_savings = (
                    monthly_infra_cost * (percentage / 100) * 0.5
                )  # 50% correlation
                annual_savings = monthly_savings * 12

                # Add operational efficiency gains
                ops_savings = self._calculate_ops_efficiency_gain(percentage)

                total_value = annual_savings + ops_savings

                return {
                    "total_value": int(total_value),
                    "currency": "USD",
                    "period": "yearly",
                    "type": ValueType.PRODUCTIVITY_GAIN.value,
                    "confidence": self.config.medium_confidence,
                    "method": "performance_calculation",
                    "breakdown": {
                        "performance_improvement_pct": percentage,
                        "infrastructure_savings": int(annual_savings),
                        "operational_efficiency_gains": int(ops_savings),
                        "basis": f"{percentage}% performance improvement",
                    },
                }
        return None

    def _extract_automation_value(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract automation value based on manual process elimination."""
        automation_keywords = [
            r"automat(?:es?|ed|ing)",
            r"eliminates?\s+manual",
            r"no\s+longer\s+(?:need|require)",
            r"replaces?\s+manual",
            r"CI/CD",
            r"deployment\s+pipeline",
        ]

        if any(
            re.search(pattern, description, re.IGNORECASE)
            for pattern in automation_keywords
        ):
            # Estimate based on PR size and typical automation benefits
            files_changed = metrics.get(
                "changed_files", metrics.get("files_changed", 1)
            )
            lines_changed = metrics.get("additions", 0) + metrics.get("deletions", 0)

            # Automation value scales with complexity
            base_automation_value = 5000  # Base value for simple automation

            if files_changed >= 10 or lines_changed >= 500:
                automation_value = base_automation_value * 3  # Complex automation
                confidence = self.config.high_confidence
            elif files_changed >= 5 or lines_changed >= 200:
                automation_value = base_automation_value * 2  # Medium automation
                confidence = self.config.medium_confidence
            else:
                automation_value = base_automation_value  # Simple automation
                confidence = self.config.low_confidence

            return {
                "total_value": automation_value,
                "currency": "USD",
                "period": "yearly",
                "type": ValueType.AUTOMATION.value,
                "confidence": confidence,
                "method": "automation_heuristic",
                "breakdown": {
                    "complexity_factor": files_changed * 100 + lines_changed,
                    "base_value": base_automation_value,
                    "multiplier": automation_value // base_automation_value,
                },
            }
        return None

    def _extract_quality_improvements(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract quality improvement value."""
        quality_patterns = [
            r"(?:fix|resolv|prevent).*?(\d+)\s+(?:bugs?|defects?|issues?)",
            r"(?:reduc|decreas).*?(?:by\s+)?(\d+(?:\.\d+)?)%.*?(?:bugs?|defects?|errors?)",
            r"test\s+coverage.*?(?:increas|improv).*?(\d+(?:\.\d+)?)%",
            r"(\d+(?:\.\d+)?)%.*?(?:fewer|less).*?(?:bugs?|defects?|issues?)",
        ]

        for pattern in quality_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                value = float(match.group(1))

                if "coverage" in match.group(0).lower():
                    # Test coverage improvement
                    defects_prevented = (
                        value * 0.1
                    )  # 10% coverage ≈ 1 defect prevented per month
                    annual_value = defects_prevented * 12 * self.config.defect_fix_cost
                else:
                    # Direct defect reduction
                    if "%" in match.group(0):
                        # Percentage reduction
                        baseline_defects_monthly = (
                            5  # Assume 5 defects per month baseline
                        )
                        defects_prevented = baseline_defects_monthly * (value / 100)
                    else:
                        # Absolute number
                        defects_prevented = value

                    annual_value = defects_prevented * 12 * self.config.defect_fix_cost

                return {
                    "total_value": int(annual_value),
                    "currency": "USD",
                    "period": "yearly",
                    "type": ValueType.QUALITY_IMPROVEMENT.value,
                    "confidence": self.config.medium_confidence,
                    "method": "quality_calculation",
                    "breakdown": {
                        "defects_prevented_monthly": defects_prevented,
                        "defect_fix_cost": self.config.defect_fix_cost,
                        "quality_metric": match.group(0),
                    },
                }
        return None

    def _extract_technical_debt_reduction(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract technical debt reduction value."""
        debt_keywords = [
            "technical debt",
            "refactor",
            "clean up",
            "moderniz",
            "upgrad",
            "legacy",
            "deprecated",
            "maintenance",
            "simplif",
        ]

        if any(keyword in description.lower() for keyword in debt_keywords):
            lines_changed = metrics.get("additions", 0) + metrics.get("deletions", 0)
            files_changed = metrics.get(
                "changed_files", metrics.get("files_changed", 1)
            )

            # Technical debt reduction value based on scope
            base_value = 2000
            complexity_multiplier = min(
                3.0, (lines_changed / 1000) + (files_changed / 10)
            )

            annual_value = base_value * complexity_multiplier

            return {
                "total_value": int(annual_value),
                "currency": "USD",
                "period": "yearly",
                "type": ValueType.TECHNICAL_DEBT_REDUCTION.value,
                "confidence": self.config.low_confidence,  # Hard to quantify precisely
                "method": "technical_debt_heuristic",
                "breakdown": {
                    "lines_changed": lines_changed,
                    "files_changed": files_changed,
                    "complexity_multiplier": complexity_multiplier,
                    "future_maintenance_savings": int(annual_value * 0.7),
                    "developer_productivity_gain": int(annual_value * 0.3),
                },
            }
        return None

    def _extract_risk_mitigation(
        self, description: str, metrics: Dict
    ) -> Optional[Dict]:
        """Extract risk mitigation value."""
        risk_patterns = [
            r"(?:security|vulnerability|exploit|breach)",
            r"(?:critical|urgent|high\s+priority).*?(?:fix|patch)",
            r"(?:prevent|avoid|mitigat).*?(?:incident|outage|downtime)",
            r"(?:compliance|regulation|audit|gdpr|sox)",
        ]

        for pattern in risk_patterns:
            if re.search(pattern, description, re.IGNORECASE):
                # Risk mitigation value based on severity
                if re.search(
                    r"critical|security|breach|vulnerability",
                    description,
                    re.IGNORECASE,
                ):
                    risk_value = self.config.critical_incident_cost
                    confidence = self.config.high_confidence
                elif re.search(
                    r"compliance|regulation|audit", description, re.IGNORECASE
                ):
                    risk_value = self.config.major_incident_cost
                    confidence = self.config.medium_confidence
                else:
                    risk_value = self.config.minor_incident_cost
                    confidence = self.config.low_confidence

                return {
                    "total_value": risk_value,
                    "currency": "USD",
                    "period": "one-time",
                    "type": ValueType.RISK_MITIGATION.value,
                    "confidence": confidence,
                    "method": "risk_assessment",
                    "breakdown": {
                        "risk_category": "security"
                        if "security" in description.lower()
                        else "operational",
                        "incident_cost_prevented": risk_value,
                        "risk_pattern": pattern,
                    },
                }
        return None

    def _infer_from_pr_size(self, description: str, metrics: Dict) -> Optional[Dict]:
        """Infer value from PR size when no explicit value is mentioned."""
        lines_changed = metrics.get("additions", 0) + metrics.get("deletions", 0)
        files_changed = metrics.get("changed_files", metrics.get("files_changed", 0))

        # Only for significant PRs
        if lines_changed < 50 and files_changed < 3:
            return None

        # Estimate value based on development effort
        estimated_hours = (lines_changed / 50) + (files_changed * 2)  # Rough estimate
        estimated_value = estimated_hours * self.config.mid_dev_rate

        return {
            "total_value": int(estimated_value),
            "currency": "USD",
            "period": "one-time",
            "type": ValueType.PRODUCTIVITY_GAIN.value,
            "confidence": self.config.low_confidence,
            "method": "size_inference",
            "breakdown": {
                "estimated_dev_hours": estimated_hours,
                "lines_changed": lines_changed,
                "files_changed": files_changed,
                "note": "Inferred from PR size - low confidence",
            },
        }

    def _normalize_to_annual_hours(self, hours: float, period: str) -> float:
        """Convert time periods to annual hours."""
        period_lower = period.lower()

        if "day" in period_lower:
            return hours * 250  # Working days per year
        elif "week" in period_lower:
            return hours * 52
        elif "month" in period_lower:
            return hours * 12
        elif "sprint" in period_lower:
            return hours * 26  # Bi-weekly sprints
        else:  # yearly
            return hours

    def _calculate_ops_efficiency_gain(self, performance_pct: float) -> float:
        """Calculate operational efficiency gains from performance improvements."""
        # Performance improvements reduce manual intervention, monitoring overhead, etc.
        base_ops_cost_monthly = 1000  # Base operational overhead
        efficiency_gain = base_ops_cost_monthly * (performance_pct / 100) * 0.3
        return efficiency_gain * 12  # Annual value
