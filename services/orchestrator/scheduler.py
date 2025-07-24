# services/orchestrator/scheduler.py
"""Intelligent posting scheduler for A/B testing experiments"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.orchestrator.db.models import Experiment, ExperimentVariant, HookVariant
from services.orchestrator.experiments import ExperimentManager, ExperimentStatus

logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@postgres:5432/threads_agent"
)
engine = create_engine(DATABASE_URL)


class PostingSchedule:
    """Represents a scheduled post"""

    def __init__(
        self,
        variant_id: str,
        experiment_id: str,
        persona_id: str,
        scheduled_time: datetime,
        priority: float,
        content: str,
    ):
        self.variant_id = variant_id
        self.experiment_id = experiment_id
        self.persona_id = persona_id
        self.scheduled_time = scheduled_time
        self.priority = priority
        self.content = content

    def __lt__(self, other):
        # Higher priority = posted first
        # Earlier time = posted first
        return (-self.priority, self.scheduled_time) < (
            -other.priority,
            other.scheduled_time,
        )


class ExperimentScheduler:
    """Manages posting schedule for all active experiments"""

    def __init__(self):
        self.experiment_manager = ExperimentManager()
        self.posting_queue: List[PostingSchedule] = []
        self.rate_limits = {
            # Max posts per hour per persona
            "ai-jesus": 10,
            "ai-elon": 10,
        }
        self.last_post_time: Dict[str, datetime] = {}
        self.optimal_times = {
            # Best posting hours by persona (24-hour format)
            "ai-jesus": [8, 9, 12, 17, 18, 19, 20],  # Morning, lunch, evening
            "ai-elon": [9, 10, 13, 16, 19, 20, 21, 22],  # Tech audience times
        }

    def schedule_next_posts(
        self, time_window_hours: int = 1, start_time: Optional[datetime] = None
    ) -> List[PostingSchedule]:
        """Determine what to post in next time window"""

        start_time = start_time or datetime.utcnow()
        end_time = start_time + timedelta(hours=time_window_hours)
        scheduled_posts = []

        # Get all active experiments
        active_experiments = self._get_active_experiments()

        # Track posts per persona to respect rate limits
        posts_per_persona = defaultdict(int)

        for experiment in active_experiments:
            # Check if experiment needs more data
            if not self._needs_more_samples(experiment):
                continue

            # Get posting configuration
            posts_per_hour = experiment.posts_per_hour
            posting_hours = experiment.posting_hours

            # Check if current time is within posting hours
            current_hour = start_time.hour
            if not (
                posting_hours.get("start", 0)
                <= current_hour
                < posting_hours.get("end", 24)
            ):
                continue

            # Select variants based on experiment type
            variants_to_post = self._select_variants_to_post(experiment, posts_per_hour)

            for variant in variants_to_post:
                # Check rate limits
                if posts_per_persona[experiment.persona_id] >= self.rate_limits.get(
                    experiment.persona_id, 10
                ):
                    break

                # Calculate optimal posting time
                post_time = self._calculate_optimal_time(
                    experiment.persona_id,
                    start_time,
                    end_time,
                    posts_per_persona[experiment.persona_id],
                )

                # Calculate priority
                priority = self._calculate_priority(experiment, variant)

                # Get content
                hook_variant = self._get_hook_variant(variant.variant_id)
                if not hook_variant:
                    continue

                # Create schedule
                schedule = PostingSchedule(
                    variant_id=variant.variant_id,
                    experiment_id=experiment.experiment_id,
                    persona_id=experiment.persona_id,
                    scheduled_time=post_time,
                    priority=priority,
                    content=hook_variant.hook_content,
                )

                scheduled_posts.append(schedule)
                posts_per_persona[experiment.persona_id] += 1

        # Sort by priority and time
        scheduled_posts.sort()

        # Respect minimum spacing between posts (5 minutes)
        spaced_posts = self._apply_spacing(scheduled_posts)

        return spaced_posts

    def _get_active_experiments(self) -> List[Experiment]:
        """Get all active experiments from database"""
        with Session(engine) as session:
            experiments = (
                session.query(Experiment)
                .filter_by(status=ExperimentStatus.ACTIVE)
                .all()
            )
            # Detach from session
            session.expunge_all()
            return experiments

    def _needs_more_samples(self, experiment: Experiment) -> bool:
        """Check if experiment needs more samples"""
        stats = self.experiment_manager.get_experiment_stats(experiment.experiment_id)

        # Check if we have minimum samples
        total_impressions = sum(v["impressions"] for v in stats.get("variants", []))
        if total_impressions < experiment.min_sample_size:
            return True

        # Check if we've reached significance
        if experiment.significance_achieved:
            return False

        # Check duration
        if experiment.started_at:
            duration = (
                datetime.utcnow() - experiment.started_at
            ).total_seconds() / 3600
            if duration > experiment.max_duration_hours:
                return False

        return True

    def _select_variants_to_post(
        self, experiment: Experiment, posts_per_hour: int
    ) -> List[ExperimentVariant]:
        """Select which variants to post based on experiment type"""

        with Session(engine) as session:
            variants = (
                session.query(ExperimentVariant)
                .filter_by(experiment_id=experiment.experiment_id)
                .filter(
                    ExperimentVariant.traffic_allocation > 0  # Not disabled
                )
                .all()
            )
            session.expunge_all()

        if experiment.type == "bandit":
            # Use Thompson Sampling for selection
            return self._select_bandit_variants(variants, posts_per_hour)
        else:
            # Use traffic allocation for A/B tests
            return self._select_ab_variants(variants, posts_per_hour)

    def _select_ab_variants(
        self, variants: List[ExperimentVariant], posts_per_hour: int
    ) -> List[ExperimentVariant]:
        """Select variants for A/B test based on traffic allocation"""
        selected = []

        for variant in variants:
            # Number of posts based on traffic allocation
            variant_posts = int(posts_per_hour * variant.traffic_allocation)
            if variant_posts == 0 and variant.traffic_allocation > 0:
                variant_posts = 1  # At least one post if allocated

            for _ in range(variant_posts):
                selected.append(variant)

        return selected

    def _select_bandit_variants(
        self, variants: List[ExperimentVariant], posts_per_hour: int
    ) -> List[ExperimentVariant]:
        """Select variants using Thompson Sampling"""
        from services.orchestrator.experiments import ThompsonSampling

        # Initialize bandit with performance data
        bandit = ThompsonSampling(len(variants))

        # Update with historical data
        for i, variant in enumerate(variants):
            bandit.successes[i] = variant.engagements_total + 1
            bandit.failures[i] = (
                variant.impressions_total - variant.engagements_total + 1
            )

        # Select variants
        selected = []
        for _ in range(posts_per_hour):
            idx = bandit.select_variant()
            selected.append(variants[idx])

        return selected

    def _calculate_optimal_time(
        self,
        persona_id: str,
        start_time: datetime,
        end_time: datetime,
        posts_already_scheduled: int,
    ) -> datetime:
        """Calculate optimal posting time within window"""

        # Get optimal hours for persona
        optimal_hours = self.optimal_times.get(persona_id, list(range(9, 21)))

        # Find hours within our window
        current_hour = start_time.hour
        window_hours = []

        for h in range(int((end_time - start_time).total_seconds() / 3600) + 1):
            hour = (current_hour + h) % 24
            if hour in optimal_hours:
                window_hours.append(hour)

        if not window_hours:
            # No optimal hours in window, use middle of window
            return start_time + (end_time - start_time) / 2

        # Select hour (rotate through optimal hours)
        selected_hour = window_hours[posts_already_scheduled % len(window_hours)]

        # Add some randomness within the hour (0-45 minutes)
        import random

        minutes = random.randint(0, 45)

        # Calculate actual time
        if selected_hour >= current_hour:
            post_time = start_time.replace(hour=selected_hour, minute=minutes, second=0)
        else:
            # Next day
            post_time = (start_time + timedelta(days=1)).replace(
                hour=selected_hour, minute=minutes, second=0
            )

        # Ensure within window
        if post_time < start_time:
            post_time = start_time + timedelta(minutes=5)
        elif post_time > end_time:
            post_time = end_time - timedelta(minutes=5)

        return post_time

    def _calculate_priority(
        self, experiment: Experiment, variant: ExperimentVariant
    ) -> float:
        """Calculate posting priority (higher = more urgent)"""

        priority = 0.0

        # 1. Experiments closer to significance get higher priority
        stats = self.experiment_manager.get_experiment_stats(experiment.experiment_id)
        for v_stats in stats.get("variants", []):
            if v_stats["variant_id"] == variant.variant_id and "p_value" in v_stats:
                # Close to significance (p-value between 0.05 and 0.10)
                if 0.05 < v_stats["p_value"] < 0.10:
                    priority += 50

        # 2. Experiments with fewer samples get higher priority
        if variant.impressions_total < 50:
            priority += 30

        # 3. High-performing variants get higher priority
        if variant.impressions_total > 0:
            engagement_rate = variant.engagements_total / variant.impressions_total
            if engagement_rate > 0.06:  # Above target
                priority += 20

        # 4. Time running (newer experiments get slight priority)
        if experiment.started_at:
            hours_running = (
                datetime.utcnow() - experiment.started_at
            ).total_seconds() / 3600
            if hours_running < 24:
                priority += 10

        # 5. Control variants get slight priority to establish baseline
        if variant.is_control and variant.impressions_total < 30:
            priority += 15

        return priority

    def _get_hook_variant(self, variant_id: str) -> Optional[HookVariant]:
        """Get hook variant details"""
        with Session(engine) as session:
            variant = (
                session.query(HookVariant).filter_by(variant_id=variant_id).first()
            )
            if variant:
                session.expunge(variant)
            return variant

    def _apply_spacing(
        self, posts: List[PostingSchedule], min_spacing_minutes: int = 5
    ) -> List[PostingSchedule]:
        """Ensure minimum spacing between posts"""

        if not posts:
            return posts

        spaced_posts = [posts[0]]
        last_time = posts[0].scheduled_time

        for post in posts[1:]:
            # Check spacing from last scheduled post
            time_diff = (post.scheduled_time - last_time).total_seconds() / 60

            if time_diff < min_spacing_minutes:
                # Adjust time
                post.scheduled_time = last_time + timedelta(minutes=min_spacing_minutes)

            spaced_posts.append(post)
            last_time = post.scheduled_time

        return spaced_posts

    def execute_scheduled_post(self, schedule: PostingSchedule) -> bool:
        """Execute a scheduled post (called by Celery worker)"""

        # Update variant statistics
        with Session(engine) as session:
            variant = (
                session.query(ExperimentVariant)
                .filter_by(variant_id=schedule.variant_id)
                .first()
            )

            if variant:
                variant.posts_count += 1
                session.commit()

                # Update last post time
                self.last_post_time[schedule.persona_id] = datetime.utcnow()

                logger.info(
                    f"Posted variant {schedule.variant_id} for experiment "
                    f"{schedule.experiment_id} at {schedule.scheduled_time}"
                )
                return True

        return False
