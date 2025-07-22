# services/viral_engine/reply_magnetizer.py
from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

from prometheus_client import Counter, Histogram

# Metrics for monitoring
MAGNET_INJECTION_COUNTER = Counter(
    "reply_magnets_injected_total",
    "Total reply magnets injected",
    ["magnet_type", "persona_id"],
)
MAGNET_PERFORMANCE = Histogram(
    "reply_magnet_performance",
    "Performance of different magnet types",
    ["magnet_type"],
)


class ReplyMagnetizer:
    """
    System to inject conversation starters that maximize engagement depth.
    Uses contextual analysis to add reply magnets that feel natural.
    """

    def __init__(self) -> None:
        self.conversation_starters = {
            "question_hooks": [
                "What's your experience with this?",
                "Am I missing something here?",
                "Thoughts?",
                "What would you do differently?",
                "Anyone else notice this?",
                "Is it just me or...",
                "Curious about your take on this",
            ],
            "controversy_triggers": [
                "Unpopular opinion:",
                "Hot take:",
                "Fight me on this:",
                "Controversial but true:",
                "Here's what nobody talks about:",
                "Disagree? Let's discuss:",
                "Ready for some pushback but:",
            ],
            "engagement_calls": [
                "Drop a 🔥 if you agree",
                "Tag someone who needs this",
                "What would you add to this list?",
                "Share your story below",
                "Comment your biggest challenge",
                "RT if this hits different",
                "Save this for later",
            ],
            "curiosity_magnets": [
                "But here's the twist...",
                "The surprising part?",
                "What happened next will shock you",
                "Here's where it gets interesting",
                "Plot twist:",
                "The real question is:",
                "But wait, there's more:",
            ],
            "authority_questions": [
                "Prove me wrong",
                "Change my mind",
                "What's your data on this?",
                "Anyone have counter-examples?",
                "Who else has tested this?",
                "Results may vary, but...",
                "Your mileage may vary",
            ],
        }

        # Persona-specific styles
        self.persona_styles = {
            "ai-jesus": {
                "preferred_types": ["question_hooks", "engagement_calls"],
                "tone": "compassionate",
                "custom_magnets": [
                    "What wisdom would you add? 🙏",
                    "Share your journey below",
                    "How has this blessed your life?",
                ],
            },
            "ai-elon": {
                "preferred_types": ["controversy_triggers", "authority_questions"],
                "tone": "bold",
                "custom_magnets": [
                    "Prove the simulation wrong 🚀",
                    "Mars colonists, thoughts?",
                    "First principles thinking says...",
                ],
            },
            "default": {
                "preferred_types": ["question_hooks", "engagement_calls"],
                "tone": "neutral",
                "custom_magnets": [],
            },
        }

        # Position strategies
        self.position_strategies = {
            "ending": 0.7,  # 70% chance at end
            "middle": 0.2,  # 20% chance in middle
            "beginning": 0.1,  # 10% chance at beginning
        }

    def inject_reply_magnets(
        self,
        content: str,
        persona_id: str,
        magnet_count: int = 1,
        magnet_types: Optional[List[str]] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Inject reply magnets into content based on persona and context.

        Args:
            content: The content to enhance
            persona_id: ID of the persona
            magnet_count: Number of magnets to inject
            magnet_types: Specific types to use (optional)

        Returns:
            Tuple of (enhanced_content, magnet_metadata)
        """
        # Get persona style
        persona_style = self.persona_styles.get(
            persona_id, self.persona_styles["default"]
        )

        # Determine magnet types to use
        if not magnet_types:
            magnet_types = list(persona_style["preferred_types"])

        # Analyze content to determine best magnets
        content_analysis = self._analyze_content(content)

        # Select and inject magnets
        enhanced_content = content
        magnet_metadata = []

        for i in range(magnet_count):
            magnet_type = self._select_magnet_type(
                content_analysis, magnet_types, persona_style
            )
            magnet_text = self._select_magnet_text(
                magnet_type, persona_style, content_analysis
            )

            # Determine position
            position = self._determine_position(content_analysis, i)

            # Inject magnet
            enhanced_content, actual_position = self._inject_at_position(
                enhanced_content, magnet_text, position
            )

            # Track metadata
            metadata = {
                "magnet_type": magnet_type,
                "magnet_text": magnet_text,
                "position": actual_position,
                "position_strategy": position,
                "persona_id": persona_id,
            }
            magnet_metadata.append(metadata)

            # Update metrics
            MAGNET_INJECTION_COUNTER.labels(
                magnet_type=magnet_type, persona_id=persona_id
            ).inc()

        return enhanced_content, magnet_metadata

    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content to determine best magnet placement"""
        sentences = re.split(r"[.!?]+", content)
        sentences = [s.strip() for s in sentences if s.strip()]

        analysis = {
            "length": len(content),
            "sentence_count": len(sentences),
            "has_question": "?" in content,
            "has_list": bool(re.search(r"\d+\.|\d+\)", content)),
            "has_controversy": any(
                word in content.lower()
                for word in ["unpopular", "controversial", "nobody", "everyone"]
            ),
            "sentences": sentences,
            "last_sentence": sentences[-1] if sentences else "",
        }

        return analysis

    def _select_magnet_type(
        self,
        content_analysis: Dict[str, Any],
        allowed_types: List[str],
        persona_style: Dict[str, Any],
    ) -> str:
        """Select appropriate magnet type based on content"""
        # If content already has controversy, use question hooks
        if content_analysis["has_controversy"] and "question_hooks" in allowed_types:
            return "question_hooks"

        # If content has a list, use engagement calls
        if content_analysis["has_list"] and "engagement_calls" in allowed_types:
            return "engagement_calls"

        # Otherwise, pick from preferred types
        return random.choice(allowed_types)

    def _select_magnet_text(
        self,
        magnet_type: str,
        persona_style: Dict[str, Any],
        content_analysis: Dict[str, Any],
    ) -> str:
        """Select specific magnet text"""
        # Check for custom magnets first
        if persona_style["custom_magnets"] and random.random() < 0.3:
            return str(random.choice(persona_style["custom_magnets"]))

        # Otherwise use standard magnets
        options = self.conversation_starters.get(magnet_type, [])

        # Filter based on content
        if content_analysis["has_question"]:
            # Avoid question magnets if content already has questions
            options = [o for o in options if not o.endswith("?")]

        return random.choice(options) if options else "Thoughts?"

    def _determine_position(
        self, content_analysis: Dict[str, Any], magnet_index: int
    ) -> str:
        """Determine where to place the magnet"""
        # First magnet usually at end
        if magnet_index == 0:
            return "ending" if random.random() < 0.9 else "middle"

        # Subsequent magnets vary more
        rand = random.random()
        cumulative = 0.0

        for position, probability in self.position_strategies.items():
            cumulative += probability
            if rand < cumulative:
                return position

        return "ending"

    def _inject_at_position(
        self, content: str, magnet: str, position: str
    ) -> Tuple[str, str]:
        """Inject magnet at specified position"""
        if position == "beginning":
            # Add after first sentence
            sentences = re.split(r"([.!?]+)", content)
            if len(sentences) > 2:
                enhanced = (
                    sentences[0] + sentences[1] + f" {magnet} " + "".join(sentences[2:])
                )
                return enhanced, "after_first_sentence"
            else:
                return f"{magnet} {content}", "very_beginning"

        elif position == "middle":
            # Add in middle
            sentences = re.split(r"([.!?]+)", content)
            if len(sentences) > 4:
                mid_point = len(sentences) // 2
                enhanced = (
                    "".join(sentences[:mid_point])
                    + f" {magnet} "
                    + "".join(sentences[mid_point:])
                )
                return enhanced, "middle"
            else:
                # Fall back to ending
                return self._inject_at_position(content, magnet, "ending")

        else:  # ending
            # Add at end
            content = content.rstrip()
            if content[-1] in ".!?":
                return f"{content} {magnet}", "end"
            else:
                return f"{content}. {magnet}", "end_with_period"

    def remove_magnets(self, content: str) -> str:
        """Remove all known magnets from content (for testing)"""
        for magnet_list in self.conversation_starters.values():
            for magnet in magnet_list:
                content = content.replace(magnet, "")

        # Clean up extra spaces
        content = re.sub(r"\s+", " ", content).strip()
        return content

    def get_magnet_performance(self) -> Dict[str, Any]:
        """Get performance analytics for different magnet types"""
        # In production, this would query actual engagement metrics
        # For now, return mock data structure
        return {
            "magnet_type_performance": {
                "question_hooks": {"avg_replies": 3.2, "engagement_rate": 0.15},
                "controversy_triggers": {"avg_replies": 5.1, "engagement_rate": 0.22},
                "engagement_calls": {"avg_replies": 2.8, "engagement_rate": 0.18},
                "curiosity_magnets": {"avg_replies": 4.3, "engagement_rate": 0.20},
                "authority_questions": {"avg_replies": 6.2, "engagement_rate": 0.25},
            },
            "best_performers": ["authority_questions", "controversy_triggers"],
            "recommendations": {
                "ai-jesus": ["question_hooks", "engagement_calls"],
                "ai-elon": ["authority_questions", "controversy_triggers"],
            },
        }
