"""Price negotiation state handler."""
from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class PriceNegotiationHandler(BaseStateHandler):
    """Handles price discussions and package selection."""
    
    async def handle(self, context: ConversationContext) -> StateResponse:
        """Navigate pricing discussions towards close."""
        if self.should_escalate(context):
            return StateResponse(
                message="Let me get you our best possible deal. Our sales director will call in 10min with exclusive pricing!",
                requires_human_handoff=True,
                confidence_score=1.0
            )
        
        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)
        
        if analysis["ready_to_purchase"]:
            message = f"Perfect choice, {params['user_name']}! Here's your signup link: [link]. Use code FAST20 for 20% off! 🎉"
            suggested_state = "closing_attempt"
            confidence = 0.95
        elif analysis["wants_discount"]:
            message = self._offer_strategic_discount(analysis, params)
            suggested_state = "price_negotiation"
            confidence = 0.85
        elif analysis["comparing_packages"]:
            message = self._recommend_package(analysis, params, context)
            suggested_state = "price_negotiation"
            confidence = 0.8
        elif analysis["sticker_shock"]:
            message = self._handle_sticker_shock(params)
            suggested_state = "objection_handling"
            confidence = 0.7
        else:
            # Present packages clearly
            message = "3 options: Starter ($97/mo), Pro ($297/mo, most popular), Scale ($597/mo). Which fits your needs best?"
            suggested_state = "price_negotiation"
            confidence = 0.75
            
        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "price_discussed": True,
                "discount_offered": analysis.get("discount_requested", False),
                "package_interest": analysis.get("package_preference")
            }
        )
    
    def analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze pricing discussion signals."""
        message_lower = message.lower()
        
        # Purchase readiness
        purchase_keywords = [
            "i'll take", "sign me up", "let's do", "deal", "sold",
            "start with", "go with", "choose", "select"
        ]
        
        # Discount requests
        discount_keywords = [
            "discount", "coupon", "promo", "deal", "cheaper",
            "better price", "special offer", "save"
        ]
        
        # Package comparison
        package_keywords = {
            "starter": ["starter", "basic", "cheapest", "small", "entry"],
            "pro": ["pro", "professional", "middle", "popular", "recommended"],
            "scale": ["scale", "enterprise", "biggest", "premium", "advanced"]
        }
        
        # Sticker shock indicators
        shock_keywords = [
            "too expensive", "can't afford", "out of budget",
            "too much", "yikes", "wow that's", "seriously?"
        ]
        
        ready_to_purchase = any(kw in message_lower for kw in purchase_keywords)
        wants_discount = any(kw in message_lower for kw in discount_keywords)
        sticker_shock = any(kw in message_lower for kw in shock_keywords)
        
        # Determine package preference
        package_preference = None
        for package, keywords in package_keywords.items():
            if any(kw in message_lower for kw in keywords):
                package_preference = package
                break
        
        comparing_packages = "which" in message_lower or "difference" in message_lower or "compare" in message_lower
        
        return {
            "ready_to_purchase": ready_to_purchase,
            "wants_discount": wants_discount,
            "discount_requested": wants_discount,
            "comparing_packages": comparing_packages,
            "package_preference": package_preference,
            "sticker_shock": sticker_shock,
            "price_sensitivity": "high" if sticker_shock or wants_discount else "normal"
        }
    
    def _offer_strategic_discount(self, analysis: Dict[str, Any], params: Dict[str, Any]) -> str:
        """Offer discounts strategically."""
        if analysis.get("price_sensitivity") == "high":
            return f"I hear you, {params['user_name']}! What if we did 40% off your first 3 months? That's $58/mo to start. Deal?"
        else:
            return "I can offer 20% off with annual payment, or 30% off if you start today. Which works better?"
    
    def _recommend_package(self, analysis: Dict[str, Any], params: Dict[str, Any], context: ConversationContext) -> str:
        """Recommend the right package based on needs."""
        pain_points = context.metadata.get("pain_points", [])
        
        if "scale" in pain_points or len(pain_points) > 2:
            return "Based on your needs, Pro is perfect. It handles everything you mentioned + room to grow. Want to start there?"
        elif analysis.get("price_sensitivity") == "high":
            return "Starter gets you 80% of the value at entry price. You can always upgrade. Should we begin with that?"
        else:
            return "Pro is our sweet spot - best value, all core features, used by 73% of customers. Sound good?"
    
    def _handle_sticker_shock(self, params: Dict[str, Any]) -> str:
        """Address sticker shock with value reframing."""
        responses = [
            f"I get it, {params['user_name']}! Let's break it down: $3/day to save 2hrs/day. Still feel expensive?",
            "Think of it this way: One new customer pays for 6 months. How many customers could this bring you?",
            f"Fair reaction! What if we started with Starter + my personal success guarantee? Low risk, high reward?"
        ]
        
        # Rotate through responses based on conversation
        return responses[0]  # In production, would track which was used