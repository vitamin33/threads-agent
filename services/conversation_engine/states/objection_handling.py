"""Objection handling state handler."""

from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class ObjectionHandlingHandler(BaseStateHandler):
    """Handles common objections with specific strategies."""

    async def handle(self, context: ConversationContext) -> StateResponse:
        """Handle objections with empathy and logic."""
        if self.should_escalate(context):
            return StateResponse(
                message="I understand your concerns. Let me get our founder to address this personally. Worth 5 min?",
                requires_human_handoff=True,
                confidence_score=1.0,
            )

        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)

        # Get objection type from context or analysis
        objection_type = (
            context.metadata.get("objections_raised") or analysis["objection_type"]
        )

        if analysis["objection_resolved"]:
            message = f"Glad that makes sense now! So {params['user_name']}, ready to see how this works for you specifically?"
            suggested_state = "price_negotiation"
            confidence = 0.9
        elif analysis["multiple_objections"]:
            # Handle the strongest objection first
            message = self._handle_complex_objection(analysis["objections"], params)
            suggested_state = "objection_handling"
            confidence = 0.7
        elif objection_type:
            message = self._handle_specific_objection(objection_type, params, analysis)
            suggested_state = (
                "objection_handling"
                if not analysis["softening"]
                else "price_negotiation"
            )
            confidence = 0.8
        else:
            # No clear objection, probe
            message = "I sense some hesitation. What's your biggest concern? Price, time, or something else? I'm here to help!"
            suggested_state = "objection_handling"
            confidence = 0.6

        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "objection_handled": objection_type,
                "objection_strength": analysis["objection_strength"],
            },
        )

    def analyze_message(
        self, message: str, context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze objection severity and type."""
        message_lower = message.lower()

        # Resolution indicators
        resolution_keywords = [
            "makes sense",
            "i see",
            "got it",
            "understand",
            "fair enough",
            "good point",
            "okay",
            "alright",
            "that helps",
        ]

        # Softening indicators
        softening_keywords = [
            "but",
            "however",
            "although",
            "maybe",
            "possibly",
            "might consider",
            "could work",
            "interesting",
        ]

        # Strong objection indicators
        strong_objection_keywords = [
            "definitely not",
            "no way",
            "never",
            "absolutely not",
            "not interested",
            "waste of",
            "don't believe",
        ]

        # Objection categories (expanded)
        objection_types = {
            "price": ["expensive", "cost", "afford", "budget", "money", "cheap"],
            "time": ["busy", "no time", "later", "not now", "someday"],
            "trust": ["scam", "legit", "proof", "guarantee", "risk", "safe"],
            "need": ["don't need", "already have", "working fine", "not broken"],
            "authority": ["boss", "team", "approval", "decision", "committee"],
            "competitor": ["using", "already have", "switched from", "better than"],
        }

        # Detect objections
        found_objections = []
        for obj_type, keywords in objection_types.items():
            if any(kw in message_lower for kw in keywords):
                found_objections.append(obj_type)

        objection_resolved = any(kw in message_lower for kw in resolution_keywords)
        softening = any(kw in message_lower for kw in softening_keywords)
        strong_objection = any(kw in message_lower for kw in strong_objection_keywords)

        return {
            "objection_type": found_objections[0] if found_objections else None,
            "objections": found_objections,
            "multiple_objections": len(found_objections) > 1,
            "objection_resolved": objection_resolved,
            "softening": softening,
            "objection_strength": "strong" if strong_objection else "moderate",
            "response_sentiment": "positive" if objection_resolved else "negative",
        }

    def _handle_specific_objection(
        self, objection_type: str, params: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Generate specific objection handlers."""
        handlers = {
            "price": self._handle_price_objection(params, analysis),
            "time": self._handle_time_objection(params),
            "trust": self._handle_trust_objection(params),
            "need": self._handle_need_objection(params),
            "authority": self._handle_authority_objection(params),
            "competitor": self._handle_competitor_objection(params),
        }
        return handlers.get(
            objection_type,
            f"I hear you, {params['user_name']}. What if I told you 87% of clients had the same concern but are now our biggest fans?",
        )

    def _handle_price_objection(
        self, params: Dict[str, Any], analysis: Dict[str, Any]
    ) -> str:
        """Handle price objections."""
        if analysis["objection_strength"] == "strong":
            return "I get it - investment matters. What if you could try it for 30 days, see the ROI, then decide? Fair?"
        else:
            return f"Think of it as investing $6/day to save 2hrs daily. {params['user_name']}, what's your time worth?"

    def _handle_time_objection(self, params: Dict[str, Any]) -> str:
        """Handle time objections."""
        return "Totally understand being busy! That's why setup takes 15min and then runs on autopilot. When's your least busy day?"

    def _handle_trust_objection(self, params: Dict[str, Any]) -> str:
        """Handle trust objections."""
        return f"{params['user_name']}, skepticism is smart! How about starting with our smallest package? Zero risk, cancel anytime."

    def _handle_need_objection(self, params: Dict[str, Any]) -> str:
        """Handle need objections."""
        return "Fair! But let me ask - if you could wave a magic wand and fix ONE thing in your process, what would it be?"

    def _handle_authority_objection(self, params: Dict[str, Any]) -> str:
        """Handle authority objections."""
        return "Smart to loop them in! Want me to send a 1-page summary you can share? Makes the convo super easy."

    def _handle_competitor_objection(self, params: Dict[str, Any]) -> str:
        """Handle competitor objections."""
        return "Good you're already solving this! Quick Q - what's the ONE thing you wish your current solution did better?"

    def _handle_complex_objection(
        self, objections: list, params: Dict[str, Any]
    ) -> str:
        """Handle multiple objections."""
        if "price" in objections and "time" in objections:
            return "I hear you on both cost AND time. What if I showed you how this pays for itself while saving you hours?"
        else:
            return f"Let's tackle your biggest concern first, {params['user_name']}. Is it more about [objection1] or [objection2]?"
