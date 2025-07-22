# services/viral_engine/hook_optimizer.py
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cachetools import LRUCache  # type: ignore[import-untyped]
from prometheus_client import Counter, Histogram

# Metrics for monitoring
HOOK_GENERATION_COUNTER = Counter(
    "viral_hooks_generated_total",
    "Total hooks generated",
    ["pattern_category", "persona_id"],
)
HOOK_GENERATION_LATENCY = Histogram(
    "viral_hook_generation_seconds", "Hook generation latency"
)
PATTERN_USAGE_COUNTER = Counter(
    "viral_patterns_used_total", "Pattern usage by type", ["pattern_id", "persona_id"]
)
CACHE_HITS = Counter("viral_hook_cache_hits_total", "Cache hit rate")
CACHE_MISSES = Counter("viral_hook_cache_misses_total", "Cache miss rate")


class ViralHookEngine:
    """
    Core viral hook optimization engine that selects and generates
    high-engagement hooks using proven patterns.
    """

    def __init__(self, patterns_dir: Optional[str] = None) -> None:
        self.patterns_dir = patterns_dir or Path(__file__).parent / "patterns"
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.performance_cache: LRUCache[str, Dict[str, Any]] = LRUCache(maxsize=1000)
        self.pattern_performance: Dict[str, Dict[str, Any]] = {}

        # Time-based optimization
        self.time_preferences = {
            "morning": ["controversy", "social_proof", "emotion_triggers"],
            "lunch": ["curiosity_gap", "pattern_interrupt"],
            "afternoon": ["social_proof", "curiosity_gap"],
            "evening": ["controversy", "story_hooks", "emotion_triggers"],
            "weekend": ["story_hooks", "emotion_triggers"],
        }

        # Persona-specific preferences
        self.persona_preferences = {
            "ai-jesus": {
                "preferred_categories": [
                    "story_hooks",
                    "social_proof",
                    "curiosity_gap",
                ],
                "tone": "inspirational",
                "avoid": ["controversy"],
            },
            "ai-elon": {
                "preferred_categories": [
                    "controversy",
                    "pattern_interrupt",
                    "social_proof",
                ],
                "tone": "bold",
                "avoid": [],
            },
        }

        # Load all pattern files
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load all pattern files from the patterns directory"""
        pattern_files = [
            "controversy.json",
            "curiosity_gap.json",
            "social_proof.json",
            "pattern_interrupt.json",
            "emotion_triggers.json",
            "story_hooks.json",
        ]

        for filename in pattern_files:
            file_path = Path(self.patterns_dir) / filename
            if file_path.exists():
                try:
                    with open(file_path, "r") as f:
                        category_data = json.load(f)
                        self.patterns[category_data["category"]] = category_data
                        print(
                            f"Loaded {len(category_data['patterns'])} patterns for {category_data['category']}"
                        )
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

    def get_available_patterns(self) -> Dict[str, int]:
        """Get count of available patterns by category"""
        return {
            category: len(data["patterns"]) for category, data in self.patterns.items()
        }

    def get_pattern_categories(self) -> List[str]:
        """Get list of all available pattern categories"""
        return list(self.patterns.keys())

    def _get_current_time_context(self) -> str:
        """Determine current time context for optimization"""
        current_hour = datetime.now().hour

        if 6 <= current_hour < 11:
            return "morning"
        elif 11 <= current_hour < 14:
            return "lunch"
        elif 14 <= current_hour < 18:
            return "afternoon"
        elif 18 <= current_hour < 23:
            return "evening"
        else:
            return "night"

    def _select_optimal_patterns(
        self,
        persona_id: str,
        topic_category: Optional[str] = None,
        posting_time: Optional[str] = None,
        variant_count: int = 1,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        """Select optimal patterns based on context"""

        # Determine time context
        time_context = posting_time or self._get_current_time_context()

        # Get persona preferences
        persona_prefs = self.persona_preferences.get(
            persona_id,
            {
                "preferred_categories": list(self.patterns.keys()),
                "tone": "general",
                "avoid": [],
            },
        )

        # Get time-based preferences
        time_prefs = self.time_preferences.get(time_context, list(self.patterns.keys()))

        # Calculate category scores
        category_scores = {}
        for category in self.patterns.keys():
            if category in persona_prefs.get("avoid", []):
                continue

            score = 0.0

            # Base engagement rate
            base_er = self.patterns[category].get("avg_engagement_rate", 0.08)
            score += base_er * 100

            # Persona preference bonus
            if category in persona_prefs.get("preferred_categories", []):
                score += 20

            # Time preference bonus
            if category in time_prefs:
                score += 15

            # Topic relevance (simplified)
            if topic_category and category == "social_proof":
                score += 10

            # Add some randomness for exploration
            score += random.uniform(-5, 5)

            category_scores[category] = score

        # Select top categories
        sorted_categories = sorted(
            category_scores.items(), key=lambda x: x[1], reverse=True
        )

        selected_patterns = []
        patterns_needed = variant_count

        for category, score in sorted_categories:
            if patterns_needed <= 0:
                break

            # Select patterns from this category
            category_patterns = self.patterns[category]["patterns"]

            # Sort patterns by engagement rate
            sorted_patterns = sorted(
                category_patterns, key=lambda p: p.get("avg_er", 0.08), reverse=True
            )

            # Take top patterns from this category
            take_count = min(patterns_needed, len(sorted_patterns))
            for pattern in sorted_patterns[:take_count]:
                selected_patterns.append((category, pattern))
                patterns_needed -= 1

        return selected_patterns[:variant_count]

    def _fill_pattern_template(
        self, pattern: Dict[str, Any], base_content: str, persona_id: str
    ) -> str:
        """Fill pattern template with appropriate content"""
        template = pattern["template"]
        variables = pattern.get("variables", [])

        # Simple template filling logic (can be enhanced with AI)
        filled_template = template

        for variable in variables:
            if variable == "statement" or variable == "bold_statement":
                filled_template = filled_template.replace(
                    f"{{{variable}}}", base_content
                )
            elif variable == "time_period":
                filled_template = filled_template.replace(
                    f"{{{variable}}}",
                    random.choice(["30 days", "3 months", "1 year", "6 months"]),
                )
            elif variable == "number":
                filled_template = filled_template.replace(
                    f"{{{variable}}}", random.choice(["3", "5", "7", "10", "100"])
                )
            elif variable == "authority_figure":
                filled_template = filled_template.replace(
                    f"{{{variable}}}",
                    random.choice(
                        ["successful people", "entrepreneurs", "experts", "leaders"]
                    ),
                )
            else:
                # Use base content as fallback
                filled_template = filled_template.replace(
                    f"{{{variable}}}", base_content
                )

        return str(filled_template)

    @HOOK_GENERATION_LATENCY.time()  # type: ignore[misc]
    async def optimize_hook(
        self,
        persona_id: str,
        base_content: str,
        topic_category: Optional[str] = None,
        target_audience: Optional[str] = None,
        posting_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate optimized hook for given content"""

        # Check cache first
        cache_key = f"{persona_id}:{base_content}:{topic_category}:{posting_time}"
        if cache_key in self.performance_cache:
            CACHE_HITS.inc()
            return dict(self.performance_cache[cache_key])

        CACHE_MISSES.inc()

        # Select optimal pattern
        selected_patterns = self._select_optimal_patterns(
            persona_id=persona_id,
            topic_category=topic_category,
            posting_time=posting_time,
            variant_count=1,
        )

        if not selected_patterns:
            # Fallback to original content
            return {
                "original_hook": base_content,
                "optimized_hooks": [
                    {"content": base_content, "pattern": "original", "score": 0.05}
                ],
                "selected_pattern": "original",
                "expected_engagement_rate": 0.05,
                "optimization_reason": "No suitable patterns found",
            }

        category, pattern = selected_patterns[0]

        # Generate optimized hook
        optimized_hook = self._fill_pattern_template(pattern, base_content, persona_id)

        result = {
            "original_hook": base_content,
            "optimized_hooks": [
                {
                    "content": optimized_hook,
                    "pattern": pattern["id"],
                    "pattern_category": category,
                    "score": pattern.get("avg_er", 0.08),
                    "template": pattern["template"],
                }
            ],
            "selected_pattern": pattern["id"],
            "expected_engagement_rate": pattern.get("avg_er", 0.08),
            "optimization_reason": f"Selected {category} pattern for {posting_time or 'current'} time context",
        }

        # Update metrics
        HOOK_GENERATION_COUNTER.labels(
            pattern_category=category, persona_id=persona_id
        ).inc()

        PATTERN_USAGE_COUNTER.labels(
            pattern_id=pattern["id"], persona_id=persona_id
        ).inc()

        # Cache result
        self.performance_cache[cache_key] = result

        return result

    async def generate_variants(
        self,
        persona_id: str,
        base_content: str,
        topic_category: Optional[str] = None,
        variant_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate multiple hook variants for A/B testing"""

        # Select multiple patterns
        selected_patterns = self._select_optimal_patterns(
            persona_id=persona_id,
            topic_category=topic_category,
            variant_count=variant_count,
        )

        variants = []
        for i, (category, pattern) in enumerate(selected_patterns):
            optimized_hook = self._fill_pattern_template(
                pattern, base_content, persona_id
            )

            variant = {
                "variant_id": f"{persona_id}_{i + 1}",
                "content": optimized_hook,
                "pattern": pattern["id"],
                "pattern_category": category,
                "expected_er": pattern.get("avg_er", 0.08),
                "template": pattern["template"],
                "original_content": base_content,
            }
            variants.append(variant)

            # Update metrics
            PATTERN_USAGE_COUNTER.labels(
                pattern_id=pattern["id"], persona_id=persona_id
            ).inc()

        return variants

    async def get_pattern_performance(
        self, persona_id: str, time_period_days: int = 7
    ) -> Dict[str, Any]:
        """Get pattern performance analytics"""

        # This would typically query a database for actual performance data
        # For now, return mock analytics based on pattern definitions

        analytics = {
            "persona_id": persona_id,
            "time_period_days": time_period_days,
            "patterns_analyzed": len(
                [p for category in self.patterns.values() for p in category["patterns"]]
            ),
            "top_performing_categories": [],
            "pattern_usage_stats": {},
            "recommendation": "",
        }

        # Calculate category performance
        category_performance = []
        for category, data in self.patterns.items():
            avg_er = data.get("avg_engagement_rate", 0.08)
            pattern_count = len(data["patterns"])

            category_performance.append(
                {
                    "category": category,
                    "avg_engagement_rate": avg_er,
                    "pattern_count": pattern_count,
                    "score": avg_er * pattern_count,
                }
            )

        # Sort by performance
        category_performance.sort(key=lambda x: x["score"], reverse=True)
        analytics["top_performing_categories"] = category_performance[:3]

        # Generate recommendation
        top_category = category_performance[0]["category"]
        analytics["recommendation"] = (
            f"Focus on {top_category} patterns for {persona_id} - showing {category_performance[0]['avg_engagement_rate']:.1%} avg engagement rate"
        )

        return analytics


# Alias for compatibility
HookOptimizer = ViralHookEngine
