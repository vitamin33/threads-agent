# services/orchestrator/experiments.py
"""A/B Testing and Experiment Management System"""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.orchestrator.db.models import Base, Experiment, ExperimentVariant

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@postgres:5432/threads_agent"
)
engine = create_engine(DATABASE_URL)


class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class ExperimentType(str, Enum):
    AB_TEST = "ab_test"
    MULTI_VARIANT = "multi_variant"
    BANDIT = "bandit"


class StoppingReason(str, Enum):
    SIGNIFICANCE_REACHED = "significance_reached"
    FUTILITY = "futility"
    MAX_DURATION = "max_duration"
    POOR_PERFORMANCE = "poor_performance"
    BAYESIAN_THRESHOLD = "bayesian_threshold"
    MANUAL = "manual"


class StatisticalAnalyzer:
    """Handles all statistical calculations for experiments"""

    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_effect: float,
        power: float = 0.8,
        alpha: float = 0.05,
    ) -> int:
        """
        Calculate required sample size for desired power
        Uses two-proportion z-test formula
        """
        # Convert rates to proportions
        p1 = baseline_rate
        p2 = baseline_rate * (1 + minimum_effect)

        # Average proportion (not used in this implementation)
        # p_avg = (p1 + p2) / 2

        # Z-scores
        z_alpha = stats.norm.ppf(1 - alpha / 2)  # Two-tailed
        z_beta = stats.norm.ppf(power)

        # Sample size formula
        n = ((z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))) / (
            (p2 - p1) ** 2
        )

        return int(np.ceil(n))

    @staticmethod
    def test_significance(
        control_data: Dict[str, Any],
        variant_data: Dict[str, Any],
        test_type: str = "two_tailed",
        alpha: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Perform statistical significance test
        Returns p_value, confidence interval, and effect size
        """
        # Extract metrics
        control_successes = control_data["engagements_total"]
        control_trials = control_data["impressions_total"]
        variant_successes = variant_data["engagements_total"]
        variant_trials = variant_data["impressions_total"]

        # Calculate rates
        control_rate = control_successes / control_trials if control_trials > 0 else 0
        variant_rate = variant_successes / variant_trials if variant_trials > 0 else 0

        # Perform two-proportion z-test
        count = np.array([control_successes, variant_successes])
        nobs = np.array([control_trials, variant_trials])

        if np.any(nobs == 0):
            return {
                "p_value": 1.0,
                "confidence_interval": (0, 0),
                "effect_size": 0,
                "control_rate": control_rate,
                "variant_rate": variant_rate,
                "is_significant": False,
            }

        # Z-test for proportions
        stat, pval = stats.proportions_ztest(count, nobs)

        # Calculate confidence interval
        se = np.sqrt(
            variant_rate * (1 - variant_rate) / variant_trials
            + control_rate * (1 - control_rate) / control_trials
        )

        z_crit = stats.norm.ppf(1 - alpha / 2)
        ci_lower = (variant_rate - control_rate) - z_crit * se
        ci_upper = (variant_rate - control_rate) + z_crit * se

        # Effect size (relative lift)
        effect_size = (
            (variant_rate - control_rate) / control_rate if control_rate > 0 else 0
        )

        return {
            "p_value": pval,
            "confidence_interval": (ci_lower, ci_upper),
            "effect_size": effect_size,
            "control_rate": control_rate,
            "variant_rate": variant_rate,
            "is_significant": pval < alpha,
            "z_statistic": stat,
        }

    @staticmethod
    def calculate_bayesian_probability(
        control_metrics: Dict[str, Any],
        variant_metrics: Dict[str, Any],
        num_simulations: int = 10000,
    ) -> float:
        """
        Calculate probability that variant is better than control
        Using Beta distributions for Bayesian analysis
        """
        # Beta parameters for control
        alpha_c = control_metrics["engagements_total"] + 1
        beta_c = (
            control_metrics["impressions_total"]
            - control_metrics["engagements_total"]
            + 1
        )

        # Beta parameters for variant
        alpha_v = variant_metrics["engagements_total"] + 1
        beta_v = (
            variant_metrics["impressions_total"]
            - variant_metrics["engagements_total"]
            + 1
        )

        # Monte Carlo simulation
        control_samples = np.random.beta(alpha_c, beta_c, num_simulations)
        variant_samples = np.random.beta(alpha_v, beta_v, num_simulations)

        # Probability that variant > control
        prob_variant_better = np.mean(variant_samples > control_samples)

        return prob_variant_better

    @staticmethod
    def sequential_testing(
        control_data: List[bool],
        variant_data: List[bool],
        alpha: float = 0.05,
        beta: float = 0.20,
    ) -> Tuple[Optional[str], float]:
        """
        Sequential probability ratio test for continuous monitoring
        Returns: (decision, likelihood_ratio)
        decision can be None, 'control', or 'variant'
        """
        if not control_data or not variant_data:
            return None, 0.0

        # Calculate cumulative success rates
        control_rate = np.mean(control_data)
        variant_rate = np.mean(variant_data)

        if control_rate == variant_rate:
            return None, 1.0

        # Log likelihood ratio
        llr = 0
        for c, v in zip(control_data, variant_data):
            if c and v:
                llr += np.log(variant_rate / control_rate)
            elif not c and not v:
                llr += np.log((1 - variant_rate) / (1 - control_rate))

        # Decision boundaries
        upper_bound = np.log((1 - beta) / alpha)
        lower_bound = np.log(beta / (1 - alpha))

        if llr >= upper_bound:
            return "variant", np.exp(llr)
        elif llr <= lower_bound:
            return "control", np.exp(llr)
        else:
            return None, np.exp(llr)


class ThompsonSampling:
    """Multi-armed bandit using Thompson Sampling"""

    def __init__(self, n_variants: int):
        self.n_variants = n_variants
        self.successes = np.ones(n_variants)  # Prior: Beta(1,1)
        self.failures = np.ones(n_variants)

    def select_variant(self) -> int:
        """Sample from posterior and select best variant"""
        samples = [
            np.random.beta(self.successes[i], self.failures[i])
            for i in range(self.n_variants)
        ]
        return int(np.argmax(samples))

    def update(self, variant_idx: int, success: bool) -> None:
        """Update posterior with new observation"""
        if success:
            self.successes[variant_idx] += 1
        else:
            self.failures[variant_idx] += 1

    def get_win_probabilities(self, num_simulations: int = 10000) -> List[float]:
        """Calculate probability each variant is best"""
        samples = np.zeros((num_simulations, self.n_variants))

        for i in range(self.n_variants):
            samples[:, i] = np.random.beta(
                self.successes[i], self.failures[i], num_simulations
            )

        best_variants = np.argmax(samples, axis=1)
        win_probs = [np.mean(best_variants == i) for i in range(self.n_variants)]

        return win_probs


class ExperimentManager:
    """Manages experiment lifecycle and operations"""

    def __init__(self):
        self.analyzer = StatisticalAnalyzer()

    def create_experiment(
        self,
        name: str,
        variant_ids: List[str],
        persona_id: str,
        experiment_type: ExperimentType = ExperimentType.AB_TEST,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new experiment"""

        experiment_id = str(uuid.uuid4())
        config = config or {}

        with Session(engine) as session:
            # Create experiment
            experiment = Experiment(
                experiment_id=experiment_id,
                name=name,
                persona_id=persona_id,
                status=ExperimentStatus.DRAFT,
                type=experiment_type,
                min_sample_size=config.get("min_sample_size", 100),
                max_duration_hours=config.get("max_duration_hours", 72),
                confidence_level=config.get("confidence_level", 0.95),
                power=config.get("power", 0.8),
                posts_per_hour=config.get("posts_per_hour", 2),
                posting_hours=config.get("posting_hours", {"start": 9, "end": 21}),
            )
            session.add(experiment)

            # Add variants
            for i, variant_id in enumerate(variant_ids):
                exp_variant = ExperimentVariant(
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    is_control=(i == 0),  # First variant is control
                    traffic_allocation=1.0 / len(variant_ids),
                )
                session.add(exp_variant)

            session.commit()

        return experiment_id

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment"""
        with Session(engine) as session:
            experiment = (
                session.query(Experiment).filter_by(experiment_id=experiment_id).first()
            )

            if not experiment or experiment.status != ExperimentStatus.DRAFT:
                return False

            experiment.status = ExperimentStatus.ACTIVE
            experiment.started_at = datetime.utcnow()
            session.commit()

        return True

    def get_experiment_stats(self, experiment_id: str) -> Dict[str, Any]:
        """Get current experiment statistics"""
        with Session(engine) as session:
            experiment = (
                session.query(Experiment).filter_by(experiment_id=experiment_id).first()
            )

            if not experiment:
                return {}

            variants = (
                session.query(ExperimentVariant)
                .filter_by(experiment_id=experiment_id)
                .all()
            )

            # Get control and treatment data
            control = next((v for v in variants if v.is_control), None)
            treatments = [v for v in variants if not v.is_control]

            results = {
                "experiment_id": experiment_id,
                "name": experiment.name,
                "status": experiment.status,
                "duration_hours": (
                    (datetime.utcnow() - experiment.started_at).total_seconds() / 3600
                    if experiment.started_at
                    else 0
                ),
                "variants": [],
            }

            # Add variant statistics
            for variant in variants:
                variant_stats = {
                    "variant_id": variant.variant_id,
                    "is_control": variant.is_control,
                    "posts_count": variant.posts_count,
                    "impressions": variant.impressions_total,
                    "engagements": variant.engagements_total,
                    "engagement_rate": (
                        variant.engagements_total / variant.impressions_total
                        if variant.impressions_total > 0
                        else 0
                    ),
                }
                results["variants"].append(variant_stats)

            # Statistical analysis if we have data
            if control and control.impressions_total >= 30:
                for treatment in treatments:
                    if treatment.impressions_total >= 30:
                        significance = self.analyzer.test_significance(
                            {
                                "engagements_total": control.engagements_total,
                                "impressions_total": control.impressions_total,
                            },
                            {
                                "engagements_total": treatment.engagements_total,
                                "impressions_total": treatment.impressions_total,
                            },
                        )

                        treatment_stats = next(
                            v
                            for v in results["variants"]
                            if v["variant_id"] == treatment.variant_id
                        )
                        treatment_stats.update(
                            {
                                "p_value": significance["p_value"],
                                "confidence_interval": significance[
                                    "confidence_interval"
                                ],
                                "effect_size": significance["effect_size"],
                                "is_significant": significance["is_significant"],
                            }
                        )

            return results

    def check_stopping_conditions(self, experiment_id: str) -> Optional[StoppingReason]:
        """Check if experiment should be stopped"""
        stats = self.get_experiment_stats(experiment_id)

        if not stats or stats["status"] != ExperimentStatus.ACTIVE:
            return None

        # Check max duration
        if stats["duration_hours"] > 72:  # Default max duration
            return StoppingReason.MAX_DURATION

        # Check for statistical significance
        for variant in stats["variants"]:
            if not variant["is_control"] and variant.get("is_significant"):
                return StoppingReason.SIGNIFICANCE_REACHED

        # Check for poor performers (< 2% engagement after 50 impressions)
        for variant in stats["variants"]:
            if variant["impressions"] > 50 and variant["engagement_rate"] < 0.02:
                # Mark variant for removal but don't stop experiment
                self._disable_variant(variant["variant_id"])

        return None

    def _disable_variant(self, variant_id: str) -> None:
        """Disable a poorly performing variant"""
        with Session(engine) as session:
            variant = (
                session.query(ExperimentVariant)
                .filter_by(variant_id=variant_id)
                .first()
            )
            if variant:
                variant.traffic_allocation = 0
                session.commit()


# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
