from enum import Enum
from typing import List


class ConversationState(Enum):
    """Enumeration of conversation states in the DM automation flow."""

    INITIAL_CONTACT = "initial_contact"
    INTEREST_QUALIFICATION = "interest_qualification"
    VALUE_PROPOSITION = "value_proposition"
    OBJECTION_HANDLING = "objection_handling"
    PRICE_NEGOTIATION = "price_negotiation"
    CLOSING_ATTEMPT = "closing_attempt"
    POST_PURCHASE = "post_purchase"


class ConversationStateMachine:
    """State machine managing 7-state conversation flows for DM automation."""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.current_state = ConversationState.INITIAL_CONTACT
        self.state_history: List[ConversationState] = [
            ConversationState.INITIAL_CONTACT
        ]

    def transition_to_next_state(self) -> None:
        """Transition to the next state in the conversation flow."""
        states = list(ConversationState)
        current_index = states.index(self.current_state)

        if current_index < len(states) - 1:
            new_state = states[current_index + 1]
            self.current_state = new_state
            self.state_history.append(new_state)

    def transition_to(self, target_state: ConversationState) -> None:
        """Transition directly to a specific state."""
        self.current_state = target_state
        self.state_history.append(target_state)
