"""Closing attempt state handler."""
from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class ClosingAttemptHandler(BaseStateHandler):
    """Handles the closing phase of the sale."""
    
    async def handle(self, context: ConversationContext) -> StateResponse:
        """Execute the close with urgency and clarity."""
        if self.should_escalate(context):
            return StateResponse(
                message="I'll have our onboarding specialist call you right now to get you started personally!",
                requires_human_handoff=True,
                confidence_score=1.0
            )
        
        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)
        
        if analysis["purchase_confirmed"]:
            message = f"🎉 Welcome aboard, {params['user_name']}! Check your DM for login details. Quick start call tomorrow at 2pm?"
            suggested_state = "post_purchase"
            confidence = 1.0
        elif analysis["last_minute_objection"]:
            message = self._handle_last_minute_objection(analysis["objection_type"], params)
            suggested_state = "objection_handling"
            confidence = 0.7
        elif analysis["needs_reassurance"]:
            message = self._provide_reassurance(params, context)
            suggested_state = "closing_attempt"
            confidence = 0.85
        elif analysis["going_to_think"]:
            message = self._create_urgency(params)
            suggested_state = "closing_attempt"
            confidence = 0.75
        else:
            # Final close attempt
            message = self._final_close_attempt(params, context)
            suggested_state = "closing_attempt"
            confidence = 0.8
            
        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "close_attempted": True,
                "purchase_status": "completed" if analysis["purchase_confirmed"] else "pending",
                "objections_remaining": analysis.get("objection_type")
            }
        )
    
    def analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze closing signals and barriers."""
        message_lower = message.lower()
        
        # Purchase confirmation
        confirmation_keywords = [
            "yes", "let's go", "i'm in", "sign me up", "do it",
            "credit card", "payment", "purchase", "buy", "sold"
        ]
        
        # Hesitation signals
        hesitation_keywords = [
            "think about it", "sleep on it", "get back to you",
            "need to check", "let me see", "not sure", "maybe later"
        ]
        
        # Reassurance needs
        reassurance_keywords = [
            "guarantee", "sure this works", "what if", "risky",
            "commitment", "contract", "stuck", "cancel"
        ]
        
        # Last minute objections
        last_minute_patterns = {
            "price": ["still expensive", "lot of money", "budget"],
            "timing": ["bad timing", "busy period", "next month"],
            "process": ["how exactly", "complicated", "setup"],
            "trust": ["reviews", "references", "speak to someone who"]
        }
        
        purchase_confirmed = any(kw in message_lower for kw in confirmation_keywords)
        going_to_think = any(kw in message_lower for kw in hesitation_keywords)
        needs_reassurance = any(kw in message_lower for kw in reassurance_keywords)
        
        # Check for last minute objections
        objection_type = None
        last_minute_objection = False
        for obj_type, keywords in last_minute_patterns.items():
            if any(kw in message_lower for kw in keywords):
                objection_type = obj_type
                last_minute_objection = True
                break
        
        return {
            "purchase_confirmed": purchase_confirmed,
            "last_minute_objection": last_minute_objection,
            "objection_type": objection_type,
            "needs_reassurance": needs_reassurance,
            "going_to_think": going_to_think,
            "close_probability": 0.9 if purchase_confirmed else 0.5 if needs_reassurance else 0.3
        }
    
    def _handle_last_minute_objection(self, objection_type: str, params: Dict[str, Any]) -> str:
        """Address last-minute objections quickly."""
        handlers = {
            "price": "Totally get it! What if we did payment plan? Same result, easier on cash flow. Yes?",
            "timing": f"I hear you, {params['user_name']}! But every day you wait costs you money. Start small today?",
            "process": "Super simple! I'll personally walk you through. 15min screen share and you're live. Deal?",
            "trust": "Smart to verify! Here's Sarah's story: [link]. She started exactly where you are. Convinced?"
        }
        return handlers.get(objection_type, 
            "One last thing holding you back? Let's solve it right now so you can move forward!")
    
    def _provide_reassurance(self, params: Dict[str, Any], context: ConversationContext) -> str:
        """Provide final reassurance."""
        package = context.metadata.get("package_interest", "starter")
        return f"Zero risk, {params['user_name']}! 30-day guarantee + cancel anytime + personal success coach. Start {package} now?"
    
    def _create_urgency(self, params: Dict[str, Any]) -> str:
        """Create urgency without being pushy."""
        urgency_messages = [
            f"{params['user_name']}, price goes up Monday. Lock in current rate now? (You can start whenever)",
            "BTW, only 3 spots left at this price this month. Want me to hold one for you?",
            "Quick note: the 40% discount expires in 2hrs. Should I apply it to your account?"
        ]
        return urgency_messages[0]  # In production, would vary
    
    def _final_close_attempt(self, params: Dict[str, Any], context: ConversationContext) -> str:
        """Make final close attempt."""
        pain_point = context.metadata.get("pain_points", ["time"])[0]
        return f"{params['user_name']}, you mentioned {pain_point} is killing you. This fixes it. One question: Start today or stay stuck?"