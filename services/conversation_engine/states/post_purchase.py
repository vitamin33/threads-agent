"""Post-purchase state handler."""

from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class PostPurchaseHandler(BaseStateHandler):
    """Handles post-purchase onboarding and relationship building."""

    async def handle(self, context: ConversationContext) -> StateResponse:
        """Manage post-purchase experience for retention."""
        if self.should_escalate(context):
            return StateResponse(
                message="Let me get your dedicated success manager on this right away. They'll call within 10min!",
                requires_human_handoff=True,
                confidence_score=1.0,
            )

        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)

        # Determine post-purchase phase
        phase = self._determine_post_purchase_phase(context)

        if phase == "immediate":
            message = self._handle_immediate_post_purchase(analysis, params)
        elif phase == "onboarding":
            message = self._handle_onboarding(analysis, params)
        elif phase == "activation":
            message = self._handle_activation(analysis, params)
        elif phase == "success":
            message = self._handle_success_check(analysis, params)
        else:
            message = self._handle_ongoing_relationship(analysis, params)

        # Always stay in post-purchase unless escalating
        suggested_state = "post_purchase"
        confidence = 0.9 if not analysis.get("has_issues") else 0.7

        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "post_purchase_phase": phase,
                "customer_satisfaction": analysis.get("satisfaction_level", "unknown"),
                "needs_support": analysis.get("has_issues", False),
            },
        )

    def analyze_message(
        self, message: str, context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze post-purchase communication."""
        message_lower = message.lower()

        # Satisfaction indicators
        positive_keywords = [
            "love",
            "amazing",
            "awesome",
            "great",
            "fantastic",
            "working well",
            "perfect",
            "thanks",
            "appreciate",
        ]

        # Issue indicators
        issue_keywords = [
            "problem",
            "issue",
            "not working",
            "help",
            "stuck",
            "confused",
            "error",
            "broken",
            "wrong",
            "can't",
        ]

        # Support needs
        support_keywords = [
            "how do i",
            "where is",
            "can't find",
            "show me",
            "tutorial",
            "guide",
            "documentation",
            "training",
        ]

        # Success indicators
        success_keywords = [
            "results",
            "roi",
            "saved",
            "earned",
            "improved",
            "increased",
            "better",
            "growth",
            "win",
        ]

        has_issues = any(kw in message_lower for kw in issue_keywords)
        needs_support = any(kw in message_lower for kw in support_keywords)
        reporting_success = any(kw in message_lower for kw in success_keywords)
        satisfied = any(kw in message_lower for kw in positive_keywords)

        # Determine satisfaction level
        if satisfied and not has_issues:
            satisfaction_level = "high"
        elif has_issues:
            satisfaction_level = "low"
        else:
            satisfaction_level = "medium"

        return {
            "has_issues": has_issues,
            "needs_support": needs_support,
            "reporting_success": reporting_success,
            "satisfied": satisfied,
            "satisfaction_level": satisfaction_level,
            "engagement_type": "support"
            if has_issues
            else "success"
            if reporting_success
            else "general",
        }

    def _determine_post_purchase_phase(self, context: ConversationContext) -> str:
        """Determine which post-purchase phase we're in."""
        # In production, would calculate from purchase timestamp
        # For now, use metadata or default to immediate
        days_since_purchase = context.metadata.get("days_since_purchase", 0)

        if days_since_purchase == 0:
            return "immediate"
        elif days_since_purchase <= 3:
            return "onboarding"
        elif days_since_purchase <= 7:
            return "activation"
        elif days_since_purchase <= 30:
            return "success"
        else:
            return "ongoing"

    def _handle_immediate_post_purchase(
        self, analysis: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Handle immediate post-purchase (first 24h)."""
        if analysis["has_issues"]:
            return "Oh no! Let's fix that right away. What specific issue are you seeing? I'm here to help!"
        else:
            return f"🚀 {params['user_name']}, you're all set! Check email for login. Join our VIP onboarding call tomorrow?"

    def _handle_onboarding(
        self, analysis: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Handle onboarding phase (days 1-3)."""
        if analysis["needs_support"]:
            return "Great question! Here's a 2-min video showing exactly that: [link]. Need anything else?"
        elif analysis["satisfied"]:
            return f"Love hearing that, {params['user_name']}! Pro tip: Try the [advanced feature] next. Game changer!"
        else:
            return "How's the setup going? Most users are fully running by Day 2. Any blockers I can help with?"

    def _handle_activation(
        self, analysis: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Handle activation phase (days 4-7)."""
        if analysis["reporting_success"]:
            return "That's incredible! 🎉 Mind if I share your success story? Others would love to hear!"
        else:
            return f"{params['user_name']}, quick check - seeing the results you expected? Most see first wins by now!"

    def _handle_success_check(
        self, analysis: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Handle success check phase (days 8-30)."""
        if analysis["satisfied"]:
            return "Thrilled you're getting value! BTW, our power users love [advanced feature]. Want a quick demo?"
        else:
            return "30-day check in! What's working best for you? And what could be even better?"

    def _handle_ongoing_relationship(
        self, analysis: Dict[str, Any], params: Dict[str, Any]
    ) -> str:
        """Handle ongoing relationship (30+ days)."""
        if analysis["reporting_success"]:
            return f"Amazing results, {params['user_name']}! Have you thought about scaling up? Our Pro plan could 3x this..."
        else:
            return "Hey! Noticed you've been quiet. Everything running smoothly? Here if you need anything!"
