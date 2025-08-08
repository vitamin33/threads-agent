"""Initial contact state handler."""

from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class InitialContactHandler(BaseStateHandler):
    """Handles the initial contact phase of the conversation."""

    async def handle(self, context: ConversationContext) -> StateResponse:
        """Handle initial contact with personalized opener."""
        # Check for escalation
        if self.should_escalate(context):
            return StateResponse(
                message="I'll connect you with our team right away. Someone will reach out shortly!",
                requires_human_handoff=True,
                confidence_score=1.0,
            )

        # Analyze the user's response
        analysis = self.analyze_message(context.current_message, context)

        # Get personalization params
        params = self.get_personalization_params(context)

        # Generate response based on analysis
        if analysis["sentiment"] == "positive" and analysis["shows_interest"]:
            message = f"Love the enthusiasm, {params['user_name']}! 🎯 What specific challenge are you looking to solve?"
            suggested_state = "interest_qualification"
            confidence = 0.9
        elif analysis["sentiment"] == "neutral":
            message = f"Hey {params['user_name']}! Noticed you checked out our solution. What caught your eye?"
            suggested_state = "interest_qualification"
            confidence = 0.7
        else:
            message = "No worries at all! If you ever need help with [specific problem], I'm here. What's your biggest challenge right now?"
            suggested_state = "initial_contact"  # Stay in same state
            confidence = 0.5

        return StateResponse(
            message=message[:280],  # Ensure under 280 chars
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "sentiment": analysis["sentiment"],
                "user_engaged": analysis["shows_interest"],
            },
        )

    def analyze_message(
        self, message: str, context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze initial contact response for interest signals."""
        message_lower = message.lower()

        # Interest indicators
        interest_keywords = [
            "interested",
            "tell me more",
            "how does",
            "what is",
            "curious",
            "sounds good",
            "yes",
            "yeah",
            "sure",
            "pricing",
            "cost",
            "demo",
            "trial",
        ]

        # Negative indicators
        negative_keywords = [
            "not interested",
            "no thanks",
            "unsubscribe",
            "stop",
            "don't",
            "leave me alone",
            "spam",
        ]

        shows_interest = any(kw in message_lower for kw in interest_keywords)
        shows_disinterest = any(kw in message_lower for kw in negative_keywords)

        # Determine sentiment
        if shows_disinterest:
            sentiment = "negative"
        elif shows_interest:
            sentiment = "positive"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "shows_interest": shows_interest and not shows_disinterest,
            "keywords_found": [kw for kw in interest_keywords if kw in message_lower],
            "message_length": len(message),
            "response_time": context.metadata.get("response_time", 0),
        }
