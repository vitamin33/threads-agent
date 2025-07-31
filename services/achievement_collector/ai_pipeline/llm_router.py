"""Intelligent LLM routing system for optimal model selection.

Demonstrates advanced AI/ML skills:
- Multi-model orchestration
- Intelligent routing algorithms
- Performance optimization
- Cost-aware model selection
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels for model routing."""

    SIMPLE = "simple"  # Basic text processing
    MEDIUM = "medium"  # Business analysis, summarization
    COMPLEX = "complex"  # Code analysis, multi-step reasoning
    CRITICAL = "critical"  # High-stakes analysis requiring best model


class ModelCapability(Enum):
    """Model capability categories."""

    CODE_ANALYSIS = "code_analysis"
    BUSINESS_REASONING = "business_reasoning"
    CONTENT_GENERATION = "content_generation"
    MATHEMATICAL = "mathematical"
    CREATIVE = "creative"


@dataclass
class ModelSpec:
    """Specification for available models."""

    name: str
    provider: str  # openai, anthropic, etc.
    cost_per_1k_tokens: float
    avg_response_time_ms: int
    capabilities: List[ModelCapability]
    max_context_tokens: int
    quality_score: float  # 0-1, higher is better

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost for given token usage."""
        return (input_tokens + output_tokens) * self.cost_per_1k_tokens / 1000


@dataclass
class RoutingDecision:
    """Result of model routing decision."""

    selected_model: str
    reasoning: str
    expected_cost: float
    expected_quality: float
    fallback_models: List[str]


class IntelligentLLMRouter:
    """Production-ready LLM routing system for job interviews.

    Showcases:
    - Multi-model orchestration
    - Cost optimization
    - Performance monitoring
    - Intelligent fallback handling
    """

    def __init__(self):
        self.models = self._initialize_model_registry()
        self.performance_history = {}
        self.cost_optimization_enabled = True
        self.quality_threshold = 0.8

    def _initialize_model_registry(self) -> Dict[str, ModelSpec]:
        """Initialize available models with their specifications."""
        return {
            "gpt-4-turbo": ModelSpec(
                name="gpt-4-turbo",
                provider="openai",
                cost_per_1k_tokens=0.030,
                avg_response_time_ms=2500,
                capabilities=[
                    ModelCapability.CODE_ANALYSIS,
                    ModelCapability.BUSINESS_REASONING,
                    ModelCapability.MATHEMATICAL,
                ],
                max_context_tokens=128000,
                quality_score=0.95,
            ),
            "gpt-3.5-turbo": ModelSpec(
                name="gpt-3.5-turbo",
                provider="openai",
                cost_per_1k_tokens=0.002,
                avg_response_time_ms=800,
                capabilities=[
                    ModelCapability.CONTENT_GENERATION,
                    ModelCapability.BUSINESS_REASONING,
                ],
                max_context_tokens=16000,
                quality_score=0.82,
            ),
            "claude-3-sonnet": ModelSpec(
                name="claude-3-sonnet",
                provider="anthropic",
                cost_per_1k_tokens=0.015,
                avg_response_time_ms=1800,
                capabilities=[
                    ModelCapability.CODE_ANALYSIS,
                    ModelCapability.BUSINESS_REASONING,
                    ModelCapability.CREATIVE,
                ],
                max_context_tokens=200000,
                quality_score=0.93,
            ),
            "claude-3-haiku": ModelSpec(
                name="claude-3-haiku",
                provider="anthropic",
                cost_per_1k_tokens=0.00025,
                avg_response_time_ms=400,
                capabilities=[
                    ModelCapability.CONTENT_GENERATION,
                ],
                max_context_tokens=200000,
                quality_score=0.78,
            ),
        }

    async def route_request(
        self,
        task_type: str,
        complexity: TaskComplexity,
        required_capabilities: List[ModelCapability],
        context_size: int,
        quality_preference: float = 0.8,
        cost_constraint: Optional[float] = None,
    ) -> RoutingDecision:
        """Route request to optimal model based on requirements.

        Args:
            task_type: Type of task (e.g., "pr_analysis", "business_value")
            complexity: Task complexity level
            required_capabilities: Required model capabilities
            context_size: Size of input context in tokens
            quality_preference: Desired quality level (0-1)
            cost_constraint: Maximum acceptable cost per request

        Returns:
            RoutingDecision with selected model and reasoning
        """

        # Filter models by capabilities and context size
        candidate_models = self._filter_capable_models(
            required_capabilities, context_size
        )

        if not candidate_models:
            raise ValueError("No models available for required capabilities")

        # Score models based on requirements
        scored_models = []
        for model_name in candidate_models:
            score = await self._score_model(
                model_name,
                complexity,
                quality_preference,
                cost_constraint,
                context_size,
            )
            scored_models.append((model_name, score))

        # Sort by score (highest first)
        scored_models.sort(key=lambda x: x[1], reverse=True)

        selected_model = scored_models[0][0]
        fallback_models = [m[0] for m in scored_models[1:3]]  # Top 2 alternatives

        # Calculate expected metrics
        model_spec = self.models[selected_model]
        expected_cost = model_spec.calculate_cost(
            context_size, 500
        )  # Assume 500 output tokens
        expected_quality = model_spec.quality_score

        # Generate reasoning
        reasoning = self._generate_routing_reasoning(
            selected_model, complexity, required_capabilities, expected_cost
        )

        # Update performance tracking
        await self._track_routing_decision(selected_model, task_type)

        return RoutingDecision(
            selected_model=selected_model,
            reasoning=reasoning,
            expected_cost=expected_cost,
            expected_quality=expected_quality,
            fallback_models=fallback_models,
        )

    def _filter_capable_models(
        self, required_capabilities: List[ModelCapability], context_size: int
    ) -> List[str]:
        """Filter models that meet capability and context requirements."""
        capable_models = []

        for model_name, spec in self.models.items():
            # Check context size limit
            if context_size > spec.max_context_tokens:
                continue

            # Check required capabilities
            if all(cap in spec.capabilities for cap in required_capabilities):
                capable_models.append(model_name)

        return capable_models

    async def _score_model(
        self,
        model_name: str,
        complexity: TaskComplexity,
        quality_preference: float,
        cost_constraint: Optional[float],
        context_size: int,
    ) -> float:
        """Score a model based on requirements and constraints."""

        spec = self.models[model_name]
        score = 0.0

        # Quality score (weighted by preference)
        quality_weight = 0.4
        score += spec.quality_score * quality_weight * quality_preference

        # Performance score based on complexity match
        performance_weight = 0.3
        if complexity == TaskComplexity.CRITICAL:
            # Prefer highest quality models for critical tasks
            score += spec.quality_score * performance_weight
        elif complexity in [TaskComplexity.COMPLEX, TaskComplexity.MEDIUM]:
            # Balance quality and cost for medium/complex tasks
            score += (
                spec.quality_score * 0.7 + (1 - spec.cost_per_1k_tokens / 0.030) * 0.3
            ) * performance_weight
        else:  # SIMPLE
            # Prefer cost-effective models for simple tasks
            score += (1 - spec.cost_per_1k_tokens / 0.030) * performance_weight

        # Cost score (lower cost = higher score)
        cost_weight = 0.2
        expected_cost = spec.calculate_cost(context_size, 500)

        if cost_constraint and expected_cost > cost_constraint:
            score -= 1.0  # Heavy penalty for exceeding cost constraint
        else:
            # Normalize cost score (assuming max cost of $1.00)
            normalized_cost = min(expected_cost / 1.0, 1.0)
            score += (1 - normalized_cost) * cost_weight

        # Response time score (faster = higher score)
        speed_weight = 0.1
        # Normalize by maximum expected response time (3000ms)
        normalized_speed = min(spec.avg_response_time_ms / 3000, 1.0)
        score += (1 - normalized_speed) * speed_weight

        # Historical performance bonus
        historical_performance = self.performance_history.get(model_name, 1.0)
        score *= historical_performance

        return score

    def _generate_routing_reasoning(
        self,
        selected_model: str,
        complexity: TaskComplexity,
        capabilities: List[ModelCapability],
        expected_cost: float,
    ) -> str:
        """Generate human-readable reasoning for model selection."""

        spec = self.models[selected_model]

        reasoning_parts = [
            f"Selected {selected_model} for {complexity.value} task",
            f"Required capabilities: {[c.value for c in capabilities]}",
            f"Quality score: {spec.quality_score:.2f}",
            f"Expected cost: ${expected_cost:.4f}",
            f"Avg response time: {spec.avg_response_time_ms}ms",
        ]

        # Add specific reasoning based on model characteristics
        if spec.quality_score >= 0.9:
            reasoning_parts.append("High-quality model chosen for accuracy")
        if spec.cost_per_1k_tokens <= 0.005:
            reasoning_parts.append("Cost-effective option selected")
        if spec.avg_response_time_ms <= 1000:
            reasoning_parts.append("Fast response time prioritized")

        return " | ".join(reasoning_parts)

    async def _track_routing_decision(self, model_name: str, task_type: str):
        """Track routing decisions for performance optimization."""
        # In production, this would write to a database or monitoring system
        key = f"{model_name}_{task_type}"

        if key not in self.performance_history:
            self.performance_history[key] = {"decisions": 0, "successes": 0}

        self.performance_history[key]["decisions"] += 1

        logger.info(f"Routed {task_type} to {model_name}")

    async def update_model_performance(
        self,
        model_name: str,
        task_type: str,
        success: bool,
        actual_cost: float,
        actual_response_time: int,
        quality_rating: Optional[float] = None,
    ):
        """Update model performance metrics based on actual results."""

        key = f"{model_name}_{task_type}"

        if key in self.performance_history:
            if success:
                self.performance_history[key]["successes"] += 1

            # Update running averages
            spec = self.models[model_name]

            # Update cost estimate (exponential moving average)
            alpha = 0.1
            current_cost_rate = actual_cost / (
                spec.max_context_tokens * 0.1
            )  # Rough estimation
            spec.cost_per_1k_tokens = (
                alpha * current_cost_rate + (1 - alpha) * spec.cost_per_1k_tokens
            )

            # Update response time estimate
            spec.avg_response_time_ms = int(
                alpha * actual_response_time + (1 - alpha) * spec.avg_response_time_ms
            )

            # Update quality score if provided
            if quality_rating is not None:
                spec.quality_score = (
                    alpha * quality_rating + (1 - alpha) * spec.quality_score
                )

        logger.info(f"Updated performance metrics for {model_name} on {task_type}")

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics for monitoring dashboard."""

        total_decisions = sum(
            data["decisions"] for data in self.performance_history.values()
        )

        model_usage = {}
        for key, data in self.performance_history.items():
            model_name = key.split("_")[0]
            if model_name not in model_usage:
                model_usage[model_name] = {
                    "decisions": 0,
                    "successes": 0,
                    "success_rate": 0.0,
                }

            model_usage[model_name]["decisions"] += data["decisions"]
            model_usage[model_name]["successes"] += data["successes"]

            if data["decisions"] > 0:
                model_usage[model_name]["success_rate"] = (
                    data["successes"] / data["decisions"]
                )

        return {
            "total_routing_decisions": total_decisions,
            "model_usage_breakdown": model_usage,
            "available_models": len(self.models),
            "performance_optimization_enabled": self.cost_optimization_enabled,
            "quality_threshold": self.quality_threshold,
        }


# Example usage for job interviews
async def demonstrate_intelligent_routing():
    """Demonstrate intelligent LLM routing for job interviews."""

    router = IntelligentLLMRouter()

    # Scenario 1: Complex code analysis (prefer quality)
    decision1 = await router.route_request(
        task_type="code_analysis",
        complexity=TaskComplexity.COMPLEX,
        required_capabilities=[ModelCapability.CODE_ANALYSIS],
        context_size=5000,
        quality_preference=0.9,
    )

    print(f"Code Analysis: {decision1.selected_model}")
    print(f"Reasoning: {decision1.reasoning}\n")

    # Scenario 2: Simple content generation (prefer cost)
    decision2 = await router.route_request(
        task_type="content_generation",
        complexity=TaskComplexity.SIMPLE,
        required_capabilities=[ModelCapability.CONTENT_GENERATION],
        context_size=1000,
        quality_preference=0.6,
        cost_constraint=0.01,
    )

    print(f"Content Generation: {decision2.selected_model}")
    print(f"Reasoning: {decision2.reasoning}\n")

    # Show routing statistics
    stats = router.get_routing_statistics()
    print("Routing Statistics:", stats)


if __name__ == "__main__":
    asyncio.run(demonstrate_intelligent_routing())
