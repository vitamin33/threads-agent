"""Personalization engine with GPT-4o integration for response generation."""

import os
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

from services.common.openai_wrapper import chat


@dataclass
class PersonalizationRequest:
    """Request for personalized response generation."""

    state: str
    user_message: str
    conversation_history: List[Dict[str, str]]
    user_profile: Dict[str, Any]
    suggested_response: str  # From state handler
    max_length: int = 280
    tone: str = "friendly_professional"


class PersonalizationEngine:
    """Generates personalized responses using GPT-4o within 280 char limit."""

    def __init__(self):
        self.model = os.getenv("CONVERSATION_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("CONVERSATION_TEMPERATURE", "0.7"))
        self.max_retries = 3

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def generate_response(self, request: PersonalizationRequest) -> str:
        """
        Generate a personalized response using GPT-4o.

        Args:
            request: Personalization request with context

        Returns:
            Personalized message under 280 characters
        """
        prompt = self._build_prompt(request)

        try:
            # Use the common OpenAI wrapper
            response = await self._call_openai(prompt, request.max_length)

            # Ensure response is under character limit
            if len(response) > request.max_length:
                response = self._truncate_smartly(response, request.max_length)

            return response

        except Exception as e:
            # Fallback to suggested response on error
            print(f"Personalization error: {e}")
            return request.suggested_response[: request.max_length]

    def _build_prompt(self, request: PersonalizationRequest) -> str:
        """Build the prompt for GPT-4o."""
        # Get recent conversation context
        recent_history = (
            request.conversation_history[-5:] if request.conversation_history else []
        )
        history_text = "\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in recent_history]
        )

        # Extract user characteristics
        user_traits = self._extract_user_traits(request.user_profile)

        prompt = f"""You are an expert sales conversation AI managing a DM conversation.

Current State: {request.state}
User Message: {request.user_message}
Suggested Response: {request.suggested_response}

User Profile:
{json.dumps(user_traits, indent=2)}

Recent Conversation:
{history_text}

Task: Rewrite the suggested response to be more personalized and effective.

Requirements:
1. MUST be under {request.max_length} characters (this is for social media DMs)
2. Match the user's communication style: {user_traits.get("style", "casual")}
3. Sound natural and conversational, not salesy
4. Include ONE emoji max, only if appropriate
5. For {request.state} state, focus on: {self._get_state_focus(request.state)}
6. Address their specific situation, not generic
7. Create urgency without being pushy

Generate ONLY the message text, nothing else:"""

        return prompt

    async def _call_openai(self, prompt: str, max_length: int) -> str:
        """Call OpenAI API with our wrapper."""
        response = await chat(
            model=self.model,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=max_length // 3,  # Rough token to char ratio
        )
        return response.strip()

    def _extract_user_traits(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant traits for personalization."""
        return {
            "name": user_profile.get("name", "there"),
            "style": user_profile.get("communication_style", "casual"),
            "industry": user_profile.get("industry", "unknown"),
            "company_size": user_profile.get("company_size", "unknown"),
            "pain_points": user_profile.get("pain_points", []),
            "objections": user_profile.get("previous_objections", []),
            "engagement": user_profile.get("engagement_level", "medium"),
            "persona": user_profile.get("persona_type", "professional"),
        }

    def _get_state_focus(self, state: str) -> str:
        """Get the focus for each conversation state."""
        state_focus = {
            "initial_contact": "building rapport and identifying interest",
            "interest_qualification": "understanding their specific needs and pain points",
            "value_proposition": "presenting clear ROI and benefits",
            "objection_handling": "addressing concerns with empathy and logic",
            "price_negotiation": "finding the right package and creating urgency",
            "closing_attempt": "making it easy to say yes",
            "post_purchase": "ensuring success and building long-term relationship",
        }
        return state_focus.get(state.lower(), "moving the conversation forward")

    def _truncate_smartly(self, text: str, max_length: int) -> str:
        """Truncate text intelligently at sentence boundaries."""
        if len(text) <= max_length:
            return text

        # Try to cut at sentence end
        sentences = text.split(". ")
        truncated = ""

        for sentence in sentences:
            if len(truncated) + len(sentence) + 1 <= max_length:
                truncated += sentence + ". "
            else:
                break

        # If no complete sentences fit, just truncate
        if not truncated:
            return text[: max_length - 3] + "..."

        return truncated.rstrip()

    async def analyze_user_style(self, messages: List[str]) -> Dict[str, Any]:
        """Analyze user's communication style from their messages."""
        if not messages:
            return {"style": "casual", "formality": 0.5, "emoji_usage": False}

        # Simple heuristics for style detection
        combined_text = " ".join(messages).lower()

        # Formality indicators
        formal_indicators = [
            "dear",
            "regards",
            "sincerely",
            "would you",
            "could you",
            "please",
        ]
        casual_indicators = ["hey", "lol", "btw", "gonna", "wanna", "yeah", "yep"]

        formal_score = sum(1 for ind in formal_indicators if ind in combined_text)
        casual_score = sum(1 for ind in casual_indicators if ind in combined_text)

        # Emoji detection
        emoji_count = sum(1 for char in combined_text if ord(char) > 127461)

        # Determine style
        if formal_score > casual_score:
            style = "formal"
            formality = 0.8
        elif casual_score > formal_score:
            style = "casual"
            formality = 0.2
        else:
            style = "balanced"
            formality = 0.5

        return {
            "style": style,
            "formality": formality,
            "emoji_usage": emoji_count > 0,
            "avg_message_length": len(combined_text) / len(messages),
            "uses_questions": "?" in combined_text,
            "enthusiasm_level": "high" if "!" in combined_text else "normal",
        }

    def generate_fallback_response(self, state: str, context: Dict[str, Any]) -> str:
        """Generate fallback response when API fails."""
        fallbacks = {
            "initial_contact": "Hey! Noticed you checked us out. What caught your attention?",
            "interest_qualification": "What's your biggest challenge right now?",
            "value_proposition": "We can solve that in 2 weeks. Want to see how?",
            "objection_handling": "I understand your concern. What would make this a no-brainer for you?",
            "price_negotiation": "Let's find a package that fits. What's your ideal investment level?",
            "closing_attempt": "Ready to get started? Here's your special link: [signup]",
            "post_purchase": "Welcome! Let's get you set up for success. Check your email!",
        }
        return fallbacks.get(
            state, "Thanks for your message! How can I help you today?"
        )
