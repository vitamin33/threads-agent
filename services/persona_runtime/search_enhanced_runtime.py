"""
Search-Enhanced Persona Runtime
Integrates SearXNG for trend-aware content generation
"""

import logging
import os
import sys

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.searxng_wrapper import analyze_viral, find_trends
from runtime import PersonaRuntime, PostDraftState

logger = logging.getLogger(__name__)


class SearchEnhancedPersonaRuntime(PersonaRuntime):
    """Enhanced runtime with search capabilities"""

    def __init__(self, persona_id: str):
        super().__init__(persona_id)
        self.search_enabled = os.environ.get("SEARCH_ENABLED", "true").lower() == "true"

    def build_graph(self) -> StateGraph:
        """Build enhanced graph with search nodes"""
        workflow = StateGraph(PostDraftState)

        # Add all original nodes
        workflow.add_node("ingest", self.ingest)

        # Add search enhancement nodes
        if self.search_enabled:
            workflow.add_node("trend_research", self.trend_research)
            workflow.add_node("competitive_analysis", self.competitive_analysis)

        workflow.add_node("hook_llm", self.hook_llm)
        workflow.add_node("body_llm", self.body_llm)
        workflow.add_node("guardrail", self.guardrail)
        workflow.add_node("format", self.format)

        # Define flow with search integration
        workflow.set_entry_point("ingest")

        if self.search_enabled:
            workflow.add_edge("ingest", "trend_research")
            workflow.add_edge("trend_research", "competitive_analysis")
            workflow.add_edge("competitive_analysis", "hook_llm")
        else:
            workflow.add_edge("ingest", "hook_llm")

        workflow.add_edge("hook_llm", "body_llm")
        workflow.add_edge("body_llm", "guardrail")
        workflow.add_edge("guardrail", "format")
        workflow.add_edge("format", END)

        return workflow.compile()

    def trend_research(self, state: PostDraftState) -> PostDraftState:
        """Research trending topics related to user input"""
        logger.info(
            f"[{self.persona_id}] Researching trends for: {state['user_topic']}"
        )

        try:
            # Find trending topics
            trends = find_trends(state["user_topic"], timeframe="day")

            # Add trend context to state
            trend_context = "Current trending topics:\n"
            for trend in trends[:5]:  # Top 5 trends
                trend_context += f"- {trend['topic']} (score: {trend['score']})\n"

            state["trend_context"] = trend_context
            state["trending_keywords"] = [t["topic"] for t in trends[:3]]

            logger.info(f"Found {len(trends)} trending topics")

        except Exception as e:
            logger.error(f"Trend research failed: {str(e)}")
            state["trend_context"] = ""
            state["trending_keywords"] = []

        return state

    def competitive_analysis(self, state: PostDraftState) -> PostDraftState:
        """Analyze viral content patterns"""
        logger.info(f"[{self.persona_id}] Analyzing viral content patterns")

        try:
            # Analyze viral content
            viral_patterns = analyze_viral(state["user_topic"], platform="threads")

            # Extract successful patterns
            patterns_context = "Successful content patterns:\n"
            hooks = []

            for pattern in viral_patterns[:3]:  # Top 3 patterns
                patterns_context += f"- {pattern['title']}\n"
                if pattern.get("keywords"):
                    patterns_context += (
                        f"  Keywords: {', '.join(pattern['keywords'][:3])}\n"
                    )

                # Extract potential hooks
                if "?" in pattern["title"]:
                    hooks.append(pattern["title"])

            state["viral_patterns"] = patterns_context
            state["successful_hooks"] = hooks[:2]  # Store top 2 question-based hooks

            logger.info(f"Analyzed {len(viral_patterns)} viral patterns")

        except Exception as e:
            logger.error(f"Competitive analysis failed: {str(e)}")
            state["viral_patterns"] = ""
            state["successful_hooks"] = []

        return state

    def hook_llm(self, state: PostDraftState) -> PostDraftState:
        """Enhanced hook generation with search context"""
        logger.info(f"[{self.persona_id}] Generating search-enhanced hook")

        # Build enhanced prompt with search insights
        prompt = self._build_hook_prompt(state["user_topic"])

        # Add search context if available
        if state.get("trend_context"):
            prompt += f"\n\n{state['trend_context']}"

        if state.get("viral_patterns"):
            prompt += f"\n\n{state['viral_patterns']}"

        if state.get("successful_hooks"):
            prompt += "\n\nSuccessful hook examples:\n"
            for hook in state["successful_hooks"]:
                prompt += f"- {hook}\n"

        # Add trending keywords hint
        if state.get("trending_keywords"):
            prompt += f"\n\nConsider incorporating these trending keywords: {', '.join(state['trending_keywords'])}"

        prompt += (
            "\n\nGenerate a hook that leverages these insights for maximum engagement."
        )

        # Call original hook_llm logic with enhanced prompt
        state["messages"] = [HumanMessage(content=prompt)]
        return super().hook_llm(state)

    def body_llm(self, state: PostDraftState) -> PostDraftState:
        """Enhanced body generation with search context"""
        logger.info(f"[{self.persona_id}] Generating search-enhanced body")

        # Get current hook
        hook = state.get("hook", "")

        # Build enhanced prompt
        prompt = f"Write a body for this hook: {hook}\n\n"
        prompt += f"Topic: {state['user_topic']}\n\n"

        # Add viral patterns for style guidance
        if state.get("viral_patterns"):
            prompt += "Successful content style guide:\n"
            prompt += state["viral_patterns"]
            prompt += "\n"

        # Add trending context
        if state.get("trend_context"):
            prompt += "Current trends to reference:\n"
            prompt += state["trend_context"]
            prompt += "\n"

        prompt += self._build_body_prompt(hook)

        # Call original body_llm with enhanced prompt
        state["messages"] = [HumanMessage(content=prompt)]
        return super().body_llm(state)

    def format(self, state: PostDraftState) -> PostDraftState:
        """Format final output with search metadata"""
        # Call original format
        state = super().format(state)

        # Add search metadata to formatted post
        if self.search_enabled and (
            state.get("trending_keywords") or state.get("viral_patterns")
        ):
            metadata = {
                "search_enhanced": True,
                "trending_keywords": state.get("trending_keywords", []),
                "trend_score": len(state.get("trending_keywords", [])),
                "viral_patterns_used": bool(state.get("viral_patterns")),
                "competitive_analysis": bool(state.get("successful_hooks")),
            }
            state["search_metadata"] = metadata

            logger.info(f"Search enhancement metadata: {metadata}")

        return state


# Factory function to create search-enhanced runtime
def create_search_enhanced_runtime(persona_id: str) -> SearchEnhancedPersonaRuntime:
    """Create a search-enhanced persona runtime"""
    return SearchEnhancedPersonaRuntime(persona_id)


if __name__ == "__main__":
    # Example usage
    runtime = create_search_enhanced_runtime("ai-jesus")

    # Test with a topic
    initial_state = PostDraftState(
        user_topic="How AI can help with mental health",
        messages=[],
        hook="",
        body="",
        full_text="",
    )

    # Run the enhanced workflow
    result = runtime.graph.invoke(initial_state)
    print("Enhanced post generated:")
    print(result.get("full_text", "No output"))

    if result.get("search_metadata"):
        print("\nSearch metadata:")
        print(result["search_metadata"])
