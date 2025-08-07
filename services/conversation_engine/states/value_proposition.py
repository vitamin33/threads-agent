"""Value proposition state handler."""

from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class ValuePropositionHandler(BaseStateHandler):
    """Presents the value proposition tailored to user's needs."""

    async def handle(self, context: ConversationContext) -> StateResponse:
        """Present compelling value proposition."""
        if self.should_escalate(context):
            return StateResponse(
                message="I'll have our product specialist show you exactly how this works. They'll reach out within 30 min!",
                requires_human_handoff=True,
                confidence_score=1.0,
            )

        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)

        # Get pain points from previous conversation
        pain_points = context.metadata.get("pain_points", ["time"])
        primary_pain = pain_points[0] if pain_points else "efficiency"

        if analysis["ready_to_buy"]:
            message = f"Awesome! Let's get you started. Takes just 5 min. Here's the link: [signup]. Questions before we begin?"
            suggested_state = "closing_attempt"
            confidence = 0.95
        elif analysis["wants_proof"]:
            message = self._provide_social_proof(primary_pain, params)
            suggested_state = "value_proposition"  # Stay to build more value
            confidence = 0.85
        elif analysis["has_objections"]:
            objection = analysis["objection_type"]
            message = f"I hear you on {objection}. That's exactly why we offer [specific solution to objection]. Make sense?"
            suggested_state = "objection_handling"
            confidence = 0.8
        else:
            # Strengthen value prop with ROI
            message = self._calculate_roi_message(primary_pain, params)
            suggested_state = "value_proposition"
            confidence = 0.7

        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "value_presented": True,
                "objections_raised": analysis["objection_type"]
                if analysis["has_objections"]
                else None,
            },
        )

    def analyze_message(
        self, message: str, context: ConversationContext
    ) -> Dict[str, Any]:
        """Analyze response to value proposition."""
        message_lower = message.lower()

        # Buying signals
        buying_keywords = [
            "sign up",
            "let's do it",
            "i'm in",
            "ready",
            "start",
            "how do i",
            "what's next",
            "let's go",
            "sounds good",
            "perfect",
            "exactly what i need",
        ]

        # Proof request signals
        proof_keywords = [
            "proof",
            "evidence",
            "results",
            "case study",
            "testimonial",
            "who else",
            "examples",
            "show me",
            "demonstrate",
        ]

        # Objection patterns
        objection_patterns = {
            "price": ["expensive", "cost", "budget", "afford", "cheaper"],
            "time": ["don't have time", "too busy", "bandwidth", "later"],
            "trust": ["legit", "scam", "real", "guarantee", "risk"],
            "need": ["don't need", "already have", "not sure", "maybe"],
        }

        ready_to_buy = any(kw in message_lower for kw in buying_keywords)
        wants_proof = any(kw in message_lower for kw in proof_keywords)

        # Check for objections
        objection_type = None
        has_objections = False
        for obj_type, keywords in objection_patterns.items():
            if any(kw in message_lower for kw in keywords):
                objection_type = obj_type
                has_objections = True
                break

        return {
            "ready_to_buy": ready_to_buy,
            "wants_proof": wants_proof,
            "has_objections": has_objections,
            "objection_type": objection_type,
            "engagement_level": "high" if ready_to_buy else "medium",
        }

    def _provide_social_proof(self, pain_point: str, params: Dict[str, Any]) -> str:
        """Generate social proof message."""
        proof_templates = {
            "time": "[Client] saved 15hrs/week within 30 days. Their exact quote: 'Wish I found this sooner!' See case study?",
            "cost": "[Client] reduced costs by 67% in Q1. They reinvested savings into growth. Want their playbook?",
            "scale": "[Client] scaled from 100 to 10K users without adding staff. Their secret? Our automation. Details?",
            "quality": "[Client] went from 70% to 99% accuracy overnight. Zero manual work now. Want to see how?",
        }
        return proof_templates.get(
            pain_point,
            f"93% of users like you see results in Week 1. {params['user_name']}, you could be next. Ready?",
        )

    def _calculate_roi_message(self, pain_point: str, params: Dict[str, Any]) -> str:
        """Generate ROI-focused message."""
        roi_templates = {
            "time": "Quick math: 10hrs/week saved × $50/hr = $2000/mo saved. Our cost? $197/mo. That's 10x ROI!",
            "cost": "You'll save $5K+/mo on average. Investment? Under $500/mo. Do the math - it's a no-brainer!",
            "scale": "Handle 10x volume with same team. Revenue potential? $50K+/mo. Cost? Less than 1 employee.",
            "quality": "Reduce errors by 95% = happier customers = 30% more revenue. ROI hits in Week 2.",
        }
        return roi_templates.get(
            pain_point,
            "Average ROI: 5x in 60 days. But honestly, can you afford NOT to automate at this point?",
        )
