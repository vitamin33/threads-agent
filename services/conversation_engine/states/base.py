"""Base state handler for conversation states."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConversationContext:
    """Context for the conversation including user profile and history."""
    conversation_id: str
    user_id: str
    user_profile: Dict[str, Any]
    message_history: List[Dict[str, Any]]
    current_message: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class StateResponse:
    """Response from a state handler."""
    message: str  # Must be under 280 characters
    suggested_next_state: Optional[str] = None
    confidence_score: float = 0.0
    requires_human_handoff: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if len(self.message) > 280:
            raise ValueError(f"Message exceeds 280 character limit: {len(self.message)} chars")


class BaseStateHandler(ABC):
    """Abstract base class for conversation state handlers."""
    
    def __init__(self):
        self.state_name = self.__class__.__name__.replace("Handler", "")
    
    @abstractmethod
    async def handle(self, context: ConversationContext) -> StateResponse:
        """
        Handle the conversation in this state.
        
        Args:
            context: The conversation context including user profile and history
            
        Returns:
            StateResponse with the message to send and next state suggestion
        """
        pass
    
    @abstractmethod
    def analyze_message(self, message: str, context: ConversationContext) -> Dict[str, Any]:
        """
        Analyze the user's message for intent and sentiment.
        
        Args:
            message: The user's message
            context: The conversation context
            
        Returns:
            Analysis results including intent, sentiment, and key entities
        """
        pass
    
    def should_escalate(self, context: ConversationContext) -> bool:
        """
        Determine if the conversation should be escalated to a human.
        
        Args:
            context: The conversation context
            
        Returns:
            True if human handoff is needed
        """
        # Default escalation triggers
        escalation_keywords = [
            "speak to human", "real person", "agent", "manager",
            "this is stupid", "you're useless", "lawsuit", "scam",
            "refund", "cancel", "complaint"
        ]
        
        message_lower = context.current_message.lower()
        return any(keyword in message_lower for keyword in escalation_keywords)
    
    def get_personalization_params(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Extract personalization parameters from context.
        
        Args:
            context: The conversation context
            
        Returns:
            Dictionary of personalization parameters
        """
        return {
            "user_name": context.user_profile.get("name", "there"),
            "communication_style": context.user_profile.get("communication_style", "casual"),
            "interests": context.user_profile.get("interests", []),
            "previous_objections": context.user_profile.get("objections", []),
            "engagement_level": context.user_profile.get("engagement_level", "medium"),
        }