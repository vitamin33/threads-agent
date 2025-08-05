"""Interest qualification state handler."""
from typing import Dict, Any
from .base import BaseStateHandler, ConversationContext, StateResponse


class InterestQualificationHandler(BaseStateHandler):
    """Qualifies the user's interest and identifies their specific needs."""
    
    async def handle(self, context: ConversationContext) -> StateResponse:
        """Qualify interest and identify pain points."""
        if self.should_escalate(context):
            return StateResponse(
                message="Let me get someone who can better help with your specific needs. One moment!",
                requires_human_handoff=True,
                confidence_score=1.0
            )
        
        analysis = self.analyze_message(context.current_message, context)
        params = self.get_personalization_params(context)
        
        # Route based on identified pain points
        if analysis["has_clear_pain_point"]:
            pain_point = analysis["pain_points"][0]
            message = f"Ah, {pain_point} is exactly what we help with! In fact, we helped [Company] achieve [Result]. Want details?"
            suggested_state = "value_proposition"
            confidence = 0.95
        elif analysis["asking_questions"]:
            # Answer their question concisely
            message = self._answer_common_question(analysis["question_type"], params)
            suggested_state = "interest_qualification"  # Stay to gather more info
            confidence = 0.8
        elif analysis["shows_urgency"]:
            message = f"I hear the urgency, {params['user_name']}! Let's cut to the chase - we can solve this in 2 weeks. Should we talk specifics?"
            suggested_state = "value_proposition"
            confidence = 0.85
        else:
            # Probe deeper
            message = "What's the biggest bottleneck in your current process? (Most say it's either time, cost, or quality)"
            suggested_state = "interest_qualification"
            confidence = 0.6
            
        return StateResponse(
            message=message[:280],
            suggested_next_state=suggested_state,
            confidence_score=confidence,
            metadata={
                "pain_points": analysis["pain_points"],
                "urgency_level": analysis["urgency_level"]
            }
        )
    
    def analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """Analyze message for pain points and qualification signals."""
        message_lower = message.lower()
        
        # Common pain points
        pain_point_patterns = {
            "time": ["too much time", "time consuming", "takes forever", "slow", "hours"],
            "cost": ["expensive", "costs too much", "budget", "afford", "price"],
            "complexity": ["complicated", "complex", "difficult", "hard to", "confusing"],
            "scale": ["scaling", "growth", "volume", "capacity", "bandwidth"],
            "quality": ["mistakes", "errors", "quality issues", "inconsistent", "unreliable"]
        }
        
        # Identify pain points
        pain_points = []
        for category, keywords in pain_point_patterns.items():
            if any(kw in message_lower for kw in keywords):
                pain_points.append(category)
        
        # Check for questions
        question_indicators = ["?", "how", "what", "when", "where", "why", "can you", "do you"]
        asking_questions = any(ind in message_lower for ind in question_indicators)
        
        # Urgency indicators
        urgency_keywords = ["asap", "urgent", "immediately", "right now", "today", "this week", "deadline"]
        urgency_level = "high" if any(kw in message_lower for kw in urgency_keywords) else "normal"
        
        # Determine question type if asking
        question_type = None
        if asking_questions:
            if "how much" in message_lower or "cost" in message_lower or "price" in message_lower:
                question_type = "pricing"
            elif "how long" in message_lower or "when" in message_lower:
                question_type = "timeline"
            elif "how does" in message_lower or "how it works" in message_lower:
                question_type = "process"
            else:
                question_type = "general"
        
        return {
            "has_clear_pain_point": len(pain_points) > 0,
            "pain_points": pain_points,
            "asking_questions": asking_questions,
            "question_type": question_type,
            "urgency_level": urgency_level,
            "shows_urgency": urgency_level == "high",
            "engagement_score": len(message) / 10  # Simple engagement metric
        }
    
    def _answer_common_question(self, question_type: str, params: Dict[str, Any]) -> str:
        """Generate concise answers to common questions."""
        answers = {
            "pricing": f"Great question! Investment starts at $X/mo. But {params['user_name']}, the real question is ROI - most see 3x return in 60 days.",
            "timeline": "Implementation takes 5-7 days. Most clients see first results within 2 weeks. Quick enough?",
            "process": "Simple 3-step process: 1) Quick setup call 2) We implement 3) You see results. Takes <1hr of your time total.",
            "general": "Happy to explain! In short: we automate [specific task] so you save 10+ hrs/week. What matters most to you?"
        }
        return answers.get(question_type, answers["general"])