"""
A/B Testing Enhanced Persona Runtime

This module enhances the persona runtime with A/B testing capabilities,
automatically optimizing content generation based on performance data.
"""

import logging
import httpx
from typing import Dict, Any, AsyncIterator
from datetime import datetime

from services.persona_runtime.runtime import FlowState, build_dag_from_persona
from services.common.metrics import record_business_metric

logger = logging.getLogger(__name__)


class ABTestingEnhancedRuntime:
    """
    Enhanced persona runtime that integrates with A/B testing for content optimization.

    This runtime automatically:
    1. Gets optimal content dimensions from A/B testing system
    2. Enhances content generation with optimized parameters
    3. Tracks content performance for continuous optimization
    """

    def __init__(self, orchestrator_url: str = "http://orchestrator:8080"):
        self.orchestrator_url = orchestrator_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_optimal_config(
        self, persona_id: str, input_text: str
    ) -> Dict[str, Any]:
        """Get optimal content configuration from A/B testing system."""
        try:
            response = await self.client.post(
                f"{self.orchestrator_url}/ab-content/optimize",
                json={
                    "persona_id": persona_id,
                    "content_type": "post",
                    "input_text": input_text,
                    "context": {
                        "timestamp": datetime.now().isoformat(),
                        "input_length": len(input_text),
                    },
                },
            )

            if response.status_code == 200:
                config = response.json()
                logger.info(
                    f"Got optimal config for persona {persona_id}: variant {config['variant_id']}"
                )
                return config
            else:
                logger.warning(f"Failed to get optimal config: {response.status_code}")
                return self._get_fallback_config(persona_id)

        except Exception as e:
            logger.error(f"Error getting optimal config: {e}")
            return self._get_fallback_config(persona_id)

    def _get_fallback_config(self, persona_id: str) -> Dict[str, Any]:
        """Fallback configuration when A/B testing is unavailable."""
        return {
            "variant_id": "fallback_variant",
            "dimensions": {
                "hook_style": "question",
                "tone": "engaging",
                "length": "medium",
            },
            "instructions": {
                "hook": "Create an engaging opening that captures attention.",
                "tone": "Maintain an engaging, dynamic tone throughout.",
                "length": "Write at an appropriate length for the topic.",
            },
            "selection_metadata": {"persona_id": persona_id, "algorithm": "fallback"},
        }

    async def track_impression(self, variant_id: str, persona_id: str) -> bool:
        """Track content impression with A/B testing system."""
        try:
            response = await self.client.post(
                f"{self.orchestrator_url}/ab-content/track",
                json={
                    "variant_id": variant_id,
                    "persona_id": persona_id,
                    "action_type": "impression",
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "source": "persona_runtime",
                    },
                },
            )

            success = response.status_code == 200
            if success:
                logger.debug(f"Tracked impression for variant {variant_id}")
            else:
                logger.warning(f"Failed to track impression: {response.status_code}")

            return success

        except Exception as e:
            logger.error(f"Error tracking impression: {e}")
            return False

    async def track_engagement(
        self,
        variant_id: str,
        persona_id: str,
        engagement_type: str = "generation_complete",
        engagement_value: float = 1.0,
    ) -> bool:
        """Track content engagement with A/B testing system."""
        try:
            response = await self.client.post(
                f"{self.orchestrator_url}/ab-content/track",
                json={
                    "variant_id": variant_id,
                    "persona_id": persona_id,
                    "action_type": "engagement",
                    "engagement_type": engagement_type,
                    "engagement_value": engagement_value,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "source": "persona_runtime",
                    },
                },
            )

            success = response.status_code == 200
            if success:
                logger.debug(
                    f"Tracked {engagement_type} engagement for variant {variant_id}"
                )
                record_business_metric("content_generation_success", 1)
            else:
                logger.warning(f"Failed to track engagement: {response.status_code}")

            return success

        except Exception as e:
            logger.error(f"Error tracking engagement: {e}")
            return False

    async def enhanced_content_generation(
        self, persona_id: str, input_text: str
    ) -> AsyncIterator[str]:
        """
        Enhanced content generation with A/B testing optimization.

        This replaces the standard persona runtime flow with A/B testing
        enhanced generation that optimizes content dimensions.
        """
        try:
            # Step 1: Get optimal configuration from A/B testing
            config = await self.get_optimal_config(persona_id, input_text)
            variant_id = config["variant_id"]
            dimensions = config["dimensions"]
            instructions = config["instructions"]

            yield f"data: {{'type': 'ab_config', 'variant_id': '{variant_id}', 'dimensions': {dimensions}}}\n\n"

            # Step 2: Track impression
            await self.track_impression(variant_id, persona_id)

            # Step 3: Build enhanced DAG with A/B testing parameters
            dag = build_dag_from_persona(persona_id)
            if dag is None:
                yield f"data: {{'type': 'error', 'message': 'Persona {persona_id} not found'}}\n\n"
                return

            # Step 4: Create enhanced state with A/B testing instructions
            enhanced_state = FlowState(
                text=input_text,
                ab_testing_config=config,
                instructions=instructions,
                dimensions=dimensions,
                variant_id=variant_id,
            )

            # Step 5: Run enhanced content generation
            generation_successful = False
            final_content = None

            try:
                async for chunk in dag.astream(enhanced_state):
                    # Stream the generation progress
                    yield f"data: {chunk}\n\n"

                    # Check if we have final content
                    if isinstance(chunk, dict) and "draft" in chunk:
                        draft = chunk.get("draft", {})
                        if "hook" in draft and "body" in draft:
                            final_content = draft
                            generation_successful = True

                # Step 6: Track successful generation
                if generation_successful and final_content:
                    await self.track_engagement(
                        variant_id,
                        persona_id,
                        "generation_complete",
                        self._calculate_content_quality(final_content),
                    )

                    yield f"data: {{'type': 'ab_tracking', 'status': 'success', 'variant_id': '{variant_id}'}}\n\n"
                else:
                    yield f"data: {{'type': 'ab_tracking', 'status': 'incomplete', 'variant_id': '{variant_id}'}}\n\n"

            except Exception as e:
                logger.error(f"Error during enhanced content generation: {e}")
                yield f"data: {{'type': 'error', 'message': 'Generation failed: {str(e)}'}}\n\n"

        except Exception as e:
            logger.error(f"Error in enhanced content generation: {e}")
            yield f"data: {{'type': 'error', 'message': 'Enhanced generation failed: {str(e)}'}}\n\n"

    def _calculate_content_quality(self, content: Dict[str, str]) -> float:
        """Calculate content quality score for engagement tracking."""
        try:
            hook = content.get("hook", "")
            body = content.get("body", "")

            # Simple quality scoring based on content characteristics
            score = 0.5  # Base score

            # Length scoring
            if 20 <= len(hook) <= 100:  # Optimal hook length
                score += 0.1
            if 50 <= len(body) <= 300:  # Optimal body length
                score += 0.1

            # Engagement indicators
            if "?" in hook:  # Questions engage readers
                score += 0.1
            if any(
                word in hook.lower()
                for word in ["why", "how", "what", "discover", "secret"]
            ):
                score += 0.1
            if body.count("!") <= 3:  # Not too many exclamations
                score += 0.1

            # Cap the score
            return min(score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating content quality: {e}")
            return 0.5

    async def cleanup(self):
        """Cleanup resources."""
        await self.client.aclose()


# Enhanced runtime factory
def create_enhanced_runtime(
    orchestrator_url: str = "http://orchestrator:8080",
) -> ABTestingEnhancedRuntime:
    """Factory function to create enhanced runtime."""
    return ABTestingEnhancedRuntime(orchestrator_url)


# Integration with existing runtime
async def run_with_ab_testing(
    persona_id: str, input_text: str, orchestrator_url: str = "http://orchestrator:8080"
) -> AsyncIterator[str]:
    """
    Run content generation with A/B testing enhancement.

    This function can be used as a drop-in replacement for the standard
    persona runtime when A/B testing optimization is desired.
    """
    enhanced_runtime = create_enhanced_runtime(orchestrator_url)

    try:
        async for chunk in enhanced_runtime.enhanced_content_generation(
            persona_id, input_text
        ):
            yield chunk
    finally:
        await enhanced_runtime.cleanup()


# Middleware for existing runtime
class ABTestingMiddleware:
    """
    Middleware that can be added to existing persona runtime flows
    to enable A/B testing without major refactoring.
    """

    def __init__(self, orchestrator_url: str = "http://orchestrator:8080"):
        self.runtime = create_enhanced_runtime(orchestrator_url)

    async def enhance_state(self, state: FlowState, persona_id: str) -> FlowState:
        """Enhance existing FlowState with A/B testing configuration."""
        try:
            input_text = state.get("text", "")
            config = await self.runtime.get_optimal_config(persona_id, input_text)

            # Add A/B testing data to state
            enhanced_state = FlowState(**state)
            enhanced_state["ab_testing_config"] = config
            enhanced_state["variant_id"] = config["variant_id"]
            enhanced_state["dimensions"] = config["dimensions"]
            enhanced_state["instructions"] = config["instructions"]

            # Track impression
            await self.runtime.track_impression(config["variant_id"], persona_id)

            return enhanced_state

        except Exception as e:
            logger.error(f"Error enhancing state with A/B testing: {e}")
            return state

    async def track_completion(self, state: FlowState, persona_id: str) -> bool:
        """Track completion of content generation."""
        try:
            variant_id = state.get("variant_id")
            if not variant_id:
                return False

            # Calculate quality if final content is available
            draft = state.get("draft", {})
            quality_score = 1.0

            if draft and "hook" in draft and "body" in draft:
                quality_score = self.runtime._calculate_content_quality(draft)

            return await self.runtime.track_engagement(
                variant_id, persona_id, "generation_complete", quality_score
            )

        except Exception as e:
            logger.error(f"Error tracking completion: {e}")
            return False

    async def cleanup(self):
        """Cleanup middleware resources."""
        await self.runtime.cleanup()
