"""
Real Experiment Management System

This module implements comprehensive experiment lifecycle management with
statistical rigor, traffic allocation, and significance monitoring.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_

from services.orchestrator.db.models import (
    Experiment,
    ExperimentEvent,
    ExperimentVariant,
    VariantPerformance,
)
from services.common.metrics import record_latency

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment status states."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventType(Enum):
    """Experiment event types."""

    CREATED = "experiment_created"
    STARTED = "experiment_started"
    PAUSED = "experiment_paused"
    RESUMED = "experiment_resumed"
    COMPLETED = "experiment_completed"
    CANCELLED = "experiment_cancelled"
    PARTICIPANT_ASSIGNED = "participant_assigned"
    IMPRESSION = "impression"
    ENGAGEMENT = "engagement"


@dataclass
class ExperimentConfig:
    """Configuration for creating a new experiment."""

    name: str
    variant_ids: List[str]
    traffic_allocation: List[float]
    target_persona: str
    success_metrics: List[str]
    duration_days: int
    description: Optional[str] = None
    control_variant_id: Optional[str] = None
    min_sample_size: Optional[int] = None
    significance_level: float = 0.05
    minimum_detectable_effect: float = 0.05
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExperimentResults:
    """Comprehensive experiment results."""

    experiment_id: str
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_days: int
    total_participants: int
    winner_variant_id: Optional[str]
    improvement_percentage: Optional[float]
    is_statistically_significant: bool
    p_value: Optional[float]
    confidence_level: float
    variant_performance: Dict[str, Dict[str, Any]]
    segment_breakdown: Optional[Dict[str, Any]]


class ExperimentManager:
    """
    Comprehensive experiment management system for A/B testing.

    Handles experiment lifecycle, traffic allocation, statistical analysis,
    and real-time monitoring with significance testing.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._active_experiments_cache = {}
        self._cache_ttl = 300  # 5 minutes

    def create_experiment(self, config: ExperimentConfig) -> str:
        """
        Create a new A/B testing experiment.

        Args:
            config: Experiment configuration

        Returns:
            Generated experiment ID

        Raises:
            ValueError: If configuration is invalid
            IntegrityError: If experiment ID already exists
        """
        try:
            # Validate configuration
            self._validate_experiment_config(config)

            # Generate unique experiment ID
            experiment_id = f"exp_{str(uuid.uuid4()).replace('-', '')[:12]}"

            # Create experiment record (store arrays as JSON for compatibility)
            experiment = Experiment(
                experiment_id=experiment_id,
                name=config.name,
                description=config.description,
                variant_ids={"values": config.variant_ids},  # Store as JSON
                traffic_allocation={
                    "values": config.traffic_allocation
                },  # Store as JSON
                control_variant_id=config.control_variant_id,
                target_persona=config.target_persona,
                success_metrics={"values": config.success_metrics},  # Store as JSON
                status=ExperimentStatus.DRAFT.value,
                duration_days=config.duration_days,
                min_sample_size=config.min_sample_size,
                significance_level=config.significance_level,
                minimum_detectable_effect=config.minimum_detectable_effect,
                created_by=config.created_by,
                experiment_metadata=config.metadata or {},
            )

            self.db_session.add(experiment)

            # Create experiment variant tracking records
            for i, variant_id in enumerate(config.variant_ids):
                exp_variant = ExperimentVariant(
                    experiment_id=experiment_id,
                    variant_id=variant_id,
                    allocated_traffic=config.traffic_allocation[i],
                    actual_traffic=0.0,
                    participants=0,
                    impressions=0,
                    conversions=0,
                    conversion_rate=0.0,
                )
                self.db_session.add(exp_variant)

            # Record creation event
            creation_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.CREATED.value,
                variant_id=config.variant_ids[
                    0
                ],  # Use first variant for creation event
                event_metadata={
                    "created_by": config.created_by,
                    "variant_count": len(config.variant_ids),
                },
            )
            self.db_session.add(creation_event)

            self.db_session.commit()

            logger.info(f"Created experiment {experiment_id}: {config.name}")
            return experiment_id

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating experiment: {e}")
            raise

    def start_experiment(self, experiment_id: str) -> bool:
        """
        Start an experiment (move from draft to active).

        Args:
            experiment_id: ID of the experiment to start

        Returns:
            True if experiment was started successfully
        """
        try:
            experiment = self._get_experiment(experiment_id)

            if not experiment:
                logger.error(f"Experiment {experiment_id} not found")
                return False

            if experiment.status != ExperimentStatus.DRAFT.value:
                logger.warning(
                    f"Cannot start experiment {experiment_id} - status: {experiment.status}"
                )
                return False

            # Update experiment status and timing
            experiment.status = ExperimentStatus.ACTIVE.value
            experiment.start_time = datetime.now(timezone.utc)
            experiment.expected_end_time = experiment.start_time + timedelta(
                days=experiment.duration_days
            )

            # Record start event
            variant_ids = experiment.variant_ids.get("values", [])
            start_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.STARTED.value,
                variant_id=experiment.control_variant_id
                or (variant_ids[0] if variant_ids else "unknown"),
                event_metadata={"start_time": experiment.start_time.isoformat()},
            )
            self.db_session.add(start_event)

            self.db_session.commit()

            # Clear cache
            self._clear_experiment_cache(experiment_id)

            logger.info(f"Started experiment {experiment_id}")
            return True

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error starting experiment {experiment_id}: {e}")
            return False

    def pause_experiment(
        self, experiment_id: str, reason: Optional[str] = None
    ) -> bool:
        """
        Pause an active experiment.

        Args:
            experiment_id: ID of the experiment to pause
            reason: Optional reason for pausing

        Returns:
            True if experiment was paused successfully
        """
        try:
            experiment = self._get_experiment(experiment_id)

            if not experiment:
                return False

            if experiment.status != ExperimentStatus.ACTIVE.value:
                logger.warning(
                    f"Cannot pause experiment {experiment_id} - status: {experiment.status}"
                )
                return False

            experiment.status = ExperimentStatus.PAUSED.value

            # Record pause event
            variant_ids = experiment.variant_ids.get("values", [])
            pause_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.PAUSED.value,
                variant_id=experiment.control_variant_id
                or (variant_ids[0] if variant_ids else "unknown"),
                event_metadata={
                    "reason": reason,
                    "paused_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.db_session.add(pause_event)

            self.db_session.commit()
            self._clear_experiment_cache(experiment_id)

            logger.info(f"Paused experiment {experiment_id}: {reason}")
            return True

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error pausing experiment {experiment_id}: {e}")
            return False

    def complete_experiment(self, experiment_id: str) -> bool:
        """
        Complete an experiment and calculate final results.

        Args:
            experiment_id: ID of the experiment to complete

        Returns:
            True if experiment was completed successfully
        """
        try:
            experiment = self._get_experiment(experiment_id)

            if not experiment:
                return False

            if experiment.status not in [
                ExperimentStatus.ACTIVE.value,
                ExperimentStatus.PAUSED.value,
            ]:
                logger.warning(
                    f"Cannot complete experiment {experiment_id} - status: {experiment.status}"
                )
                return False

            # Calculate final results
            results = self._calculate_experiment_results(experiment_id)

            # Update experiment with results
            experiment.status = ExperimentStatus.COMPLETED.value
            experiment.end_time = datetime.now(timezone.utc)
            experiment.total_participants = results.total_participants
            experiment.winner_variant_id = results.winner_variant_id
            experiment.improvement_percentage = results.improvement_percentage
            experiment.is_statistically_significant = (
                results.is_statistically_significant
            )
            experiment.p_value = results.p_value

            # Record completion event
            variant_ids = experiment.variant_ids.get("values", [])
            completion_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.COMPLETED.value,
                variant_id=experiment.control_variant_id
                or (variant_ids[0] if variant_ids else "unknown"),
                event_metadata={
                    "completed_at": experiment.end_time.isoformat(),
                    "winner": results.winner_variant_id,
                    "significant": results.is_statistically_significant,
                },
            )
            self.db_session.add(completion_event)

            self.db_session.commit()
            self._clear_experiment_cache(experiment_id)

            logger.info(
                f"Completed experiment {experiment_id} - Winner: {results.winner_variant_id}"
            )
            return True

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error completing experiment {experiment_id}: {e}")
            return False

    def assign_participant_to_variant(
        self,
        experiment_id: str,
        participant_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Assign a participant to a variant based on traffic allocation.

        Args:
            experiment_id: ID of the experiment
            participant_id: ID of the participant
            context: Additional context for assignment

        Returns:
            Assigned variant ID or None if assignment failed
        """
        try:
            experiment = self._get_experiment(experiment_id)

            if not experiment or experiment.status != ExperimentStatus.ACTIVE.value:
                return None

            # Assign variant based on traffic allocation
            assigned_variant = self._allocate_traffic(experiment, participant_id)

            if not assigned_variant:
                return None

            # Record assignment event
            assignment_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.PARTICIPANT_ASSIGNED.value,
                participant_id=participant_id,
                variant_id=assigned_variant,
                event_metadata=context or {},
            )
            self.db_session.add(assignment_event)

            # Update experiment variant participant count
            exp_variant = (
                self.db_session.query(ExperimentVariant)
                .filter_by(experiment_id=experiment_id, variant_id=assigned_variant)
                .first()
            )

            if exp_variant:
                exp_variant.participants += 1

                # Update actual traffic allocation
                total_participants = experiment.total_participants + 1
                exp_variant.actual_traffic = (
                    exp_variant.participants / total_participants
                )

            # Update total participants
            experiment.total_participants += 1

            self.db_session.commit()

            logger.debug(
                f"Assigned participant {participant_id} to variant {assigned_variant} in experiment {experiment_id}"
            )
            return assigned_variant

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error assigning participant: {e}")
            return None

    def record_experiment_engagement(
        self,
        experiment_id: str,
        participant_id: str,
        variant_id: str,
        action_taken: str,
        engagement_value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record engagement within an experiment.

        Args:
            experiment_id: ID of the experiment
            participant_id: ID of the participant
            variant_id: ID of the variant
            action_taken: Type of action (impression, like, share, etc.)
            engagement_value: Numeric value of the engagement
            metadata: Additional metadata

        Returns:
            True if engagement was recorded successfully
        """
        try:
            # Validate experiment exists
            experiment = self._get_experiment(experiment_id)
            if not experiment:
                logger.error(
                    f"Cannot record engagement - experiment {experiment_id} not found"
                )
                return False

            # Record engagement event
            engagement_event = ExperimentEvent(
                experiment_id=experiment_id,
                event_type=EventType.ENGAGEMENT.value,
                participant_id=participant_id,
                variant_id=variant_id,
                action_taken=action_taken,
                engagement_value=engagement_value,
                event_metadata=metadata or {},
            )
            self.db_session.add(engagement_event)

            # Update experiment variant performance
            exp_variant = (
                self.db_session.query(ExperimentVariant)
                .filter_by(experiment_id=experiment_id, variant_id=variant_id)
                .first()
            )

            if exp_variant:
                if action_taken in ["impression", "view"]:
                    exp_variant.impressions += 1
                elif action_taken in [
                    "like",
                    "share",
                    "comment",
                    "click",
                    "conversion",
                ]:
                    exp_variant.conversions += 1

                # Update conversion rate
                if exp_variant.impressions > 0:
                    exp_variant.conversion_rate = (
                        exp_variant.conversions / exp_variant.impressions
                    )

            self.db_session.commit()

            logger.debug(
                f"Recorded {action_taken} for participant {participant_id} in experiment {experiment_id}"
            )
            return True

        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error recording experiment engagement: {e}")
            return False

    def get_experiment_results(
        self, experiment_id: str, include_segments: bool = False
    ) -> Optional[ExperimentResults]:
        """
        Get comprehensive experiment results with statistical analysis.

        Args:
            experiment_id: ID of the experiment
            include_segments: Whether to include segment breakdown

        Returns:
            ExperimentResults object or None if not found
        """
        try:
            with record_latency("experiment_results_calculation"):
                experiment = self._get_experiment(experiment_id)

                if not experiment:
                    return None

                # Calculate results
                return self._calculate_experiment_results(
                    experiment_id, include_segments
                )

        except Exception as e:
            logger.error(f"Error getting experiment results: {e}")
            return None

    def _calculate_experiment_results(
        self, experiment_id: str, include_segments: bool = False
    ) -> ExperimentResults:
        """Calculate comprehensive experiment results."""
        experiment = self._get_experiment(experiment_id)

        # Get experiment variants with performance data
        exp_variants = (
            self.db_session.query(ExperimentVariant)
            .filter_by(experiment_id=experiment_id)
            .all()
        )

        # Build variant performance data
        variant_performance = {}
        total_participants = 0

        for exp_variant in exp_variants:
            variant_performance[exp_variant.variant_id] = {
                "participants": exp_variant.participants,
                "impressions": exp_variant.impressions,
                "conversions": exp_variant.conversions,
                "conversion_rate": exp_variant.conversion_rate,
                "allocated_traffic": exp_variant.allocated_traffic,
                "actual_traffic": exp_variant.actual_traffic,
                "confidence_lower": exp_variant.confidence_lower,
                "confidence_upper": exp_variant.confidence_upper,
            }
            total_participants += exp_variant.participants

        # Determine winner using statistical significance
        winner_variant_id, improvement_percentage, is_significant, p_value = (
            self._calculate_statistical_significance(
                exp_variants, experiment.control_variant_id
            )
        )

        # Get segment breakdown if requested
        segment_breakdown = None
        if include_segments:
            segment_breakdown = self._get_segment_breakdown(experiment_id)

        return ExperimentResults(
            experiment_id=experiment_id,
            status=experiment.status,
            start_time=experiment.start_time,
            end_time=experiment.end_time,
            duration_days=experiment.duration_days,
            total_participants=total_participants,
            winner_variant_id=winner_variant_id,
            improvement_percentage=improvement_percentage,
            is_statistically_significant=is_significant,
            p_value=p_value,
            confidence_level=1.0 - experiment.significance_level,
            variant_performance=variant_performance,
            segment_breakdown=segment_breakdown,
        )

    def _calculate_statistical_significance(
        self, exp_variants: List[ExperimentVariant], control_variant_id: Optional[str]
    ) -> Tuple[Optional[str], Optional[float], bool, Optional[float]]:
        """Calculate statistical significance and determine winner."""
        try:
            # Import scipy for statistical tests
            import scipy.stats as stats

            if len(exp_variants) < 2:
                return None, None, False, None

            # Find control and treatment variants
            control_variant = None
            treatment_variants = []

            for variant in exp_variants:
                if variant.variant_id == control_variant_id:
                    control_variant = variant
                else:
                    treatment_variants.append(variant)

            # If no control specified, use the first variant
            if control_variant is None:
                control_variant = exp_variants[0]
                treatment_variants = exp_variants[1:]

            # Perform statistical tests
            best_variant = control_variant
            best_rate = control_variant.conversion_rate
            is_significant = False
            p_value = None

            for treatment in treatment_variants:
                if treatment.impressions < 10 or control_variant.impressions < 10:
                    continue  # Skip if insufficient data

                # Two-proportion z-test
                # H0: control_rate == treatment_rate
                # H1: treatment_rate > control_rate

                n1, x1 = control_variant.impressions, control_variant.conversions
                n2, x2 = treatment.impressions, treatment.conversions

                if n1 == 0 or n2 == 0:
                    continue

                p1 = x1 / n1
                p2 = x2 / n2

                # Pooled proportion
                p_pooled = (x1 + x2) / (n1 + n2)

                # Standard error
                se = (p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2)) ** 0.5

                if se == 0:
                    continue

                # Z-score
                z_score = (p2 - p1) / se

                # Two-tailed p-value
                p_val = 2 * (1 - stats.norm.cdf(abs(z_score)))

                # Check significance
                if p_val < 0.05 and p2 > best_rate:  # Significant improvement
                    best_variant = treatment
                    best_rate = p2
                    is_significant = True
                    p_value = p_val

            # Calculate improvement percentage
            improvement_percentage = None
            if control_variant.conversion_rate > 0:
                improvement_percentage = (
                    (best_rate - control_variant.conversion_rate)
                    / control_variant.conversion_rate
                ) * 100

            return (
                best_variant.variant_id,
                improvement_percentage,
                is_significant,
                p_value,
            )

        except ImportError:
            logger.warning("scipy not available - using simple comparison")
            # Fallback to simple best rate comparison
            best_variant = max(exp_variants, key=lambda v: v.conversion_rate)
            improvement_percentage = 0.0
            return best_variant.variant_id, improvement_percentage, False, None
        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return None, None, False, None

    def _allocate_traffic(
        self, experiment: Experiment, participant_id: str
    ) -> Optional[str]:
        """Allocate traffic based on experiment configuration."""
        try:
            # Extract arrays from JSON storage
            variant_ids = experiment.variant_ids.get("values", [])
            traffic_allocation = experiment.traffic_allocation.get("values", [])

            if not variant_ids or not traffic_allocation:
                return None

            # Simple hash-based allocation for consistent assignment
            participant_hash = (
                hash(f"{experiment.experiment_id}:{participant_id}") % 10000
            )
            allocation_point = participant_hash / 10000.0

            # Find the variant based on cumulative traffic allocation
            cumulative_allocation = 0.0

            for i, variant_id in enumerate(variant_ids):
                if i < len(traffic_allocation):
                    cumulative_allocation += traffic_allocation[i]

                    if allocation_point <= cumulative_allocation:
                        return variant_id

            # Fallback to last variant
            return variant_ids[-1] if variant_ids else None

        except Exception as e:
            logger.error(f"Error allocating traffic: {e}")
            return None

    def _validate_experiment_config(self, config: ExperimentConfig):
        """Validate experiment configuration."""
        if not config.name.strip():
            raise ValueError("Experiment name cannot be empty")

        if not config.variant_ids:
            raise ValueError("At least one variant ID is required")

        if len(config.variant_ids) != len(config.traffic_allocation):
            raise ValueError("Number of variants must match traffic allocation entries")

        if abs(sum(config.traffic_allocation) - 1.0) > 0.001:
            raise ValueError("Traffic allocation must sum to 1.0")

        if config.duration_days <= 0:
            raise ValueError("Duration must be positive")

        # Verify variants exist
        for variant_id in config.variant_ids:
            variant = (
                self.db_session.query(VariantPerformance)
                .filter_by(variant_id=variant_id)
                .first()
            )
            if not variant:
                raise ValueError(f"Variant '{variant_id}' not found")

    def _get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment with caching."""
        if experiment_id in self._active_experiments_cache:
            cached_experiment, timestamp = self._active_experiments_cache[experiment_id]
            if (datetime.now().timestamp() - timestamp) < self._cache_ttl:
                return cached_experiment

        experiment = (
            self.db_session.query(Experiment)
            .filter_by(experiment_id=experiment_id)
            .first()
        )

        if experiment:
            self._active_experiments_cache[experiment_id] = (
                experiment,
                datetime.now().timestamp(),
            )

        return experiment

    def _clear_experiment_cache(self, experiment_id: str):
        """Clear cached experiment data."""
        if experiment_id in self._active_experiments_cache:
            del self._active_experiments_cache[experiment_id]

    def _get_segment_breakdown(self, experiment_id: str) -> Dict[str, Any]:
        """Get segmented analysis for experiment."""
        # For now, return a placeholder structure
        # In a full implementation, this would analyze participant segments
        return {
            "segments_analyzed": 0,
            "segment_results": {},
            "note": "Segment analysis not yet implemented",
        }

    def list_experiments(
        self,
        status: Optional[str] = None,
        target_persona: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List experiments with optional filtering.

        Args:
            status: Filter by experiment status
            target_persona: Filter by target persona
            limit: Maximum number of experiments to return

        Returns:
            List of experiment summaries
        """
        try:
            query = self.db_session.query(Experiment)

            if status:
                query = query.filter(Experiment.status == status)

            if target_persona:
                query = query.filter(Experiment.target_persona == target_persona)

            experiments = (
                query.order_by(Experiment.created_at.desc()).limit(limit).all()
            )

            result = []
            for exp in experiments:
                result.append(
                    {
                        "experiment_id": exp.experiment_id,
                        "name": exp.name,
                        "status": exp.status,
                        "target_persona": exp.target_persona,
                        "variant_count": len(exp.variant_ids),
                        "total_participants": exp.total_participants,
                        "start_time": exp.start_time,
                        "end_time": exp.end_time,
                        "duration_days": exp.duration_days,
                        "winner_variant_id": exp.winner_variant_id,
                        "is_statistically_significant": exp.is_statistically_significant,
                        "created_at": exp.created_at,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error listing experiments: {e}")
            return []

    def get_active_experiments_for_persona(self, persona_id: str) -> List[str]:
        """Get list of active experiment IDs for a specific persona."""
        try:
            experiments = (
                self.db_session.query(Experiment)
                .filter(
                    and_(
                        Experiment.status == ExperimentStatus.ACTIVE.value,
                        Experiment.target_persona == persona_id,
                    )
                )
                .all()
            )

            return [exp.experiment_id for exp in experiments]

        except Exception as e:
            logger.error(
                f"Error getting active experiments for persona {persona_id}: {e}"
            )
            return []


# Factory function
def create_experiment_manager(db_session: Session) -> ExperimentManager:
    """Factory function to create ExperimentManager instance."""
    return ExperimentManager(db_session)
