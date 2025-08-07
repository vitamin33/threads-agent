import pytest
from services.conversation_engine.state_machine import (
    ConversationStateMachine,
    ConversationState,
)


def test_conversation_state_machine_initializes_with_initial_contact_state():
    """Test that a new conversation starts in the INITIAL_CONTACT state."""
    conversation_id = "conv_123"
    state_machine = ConversationStateMachine(conversation_id)

    assert state_machine.current_state == ConversationState.INITIAL_CONTACT
    assert state_machine.conversation_id == conversation_id


def test_conversation_state_machine_transitions_from_initial_contact_to_interest_qualification():
    """Test state transition from INITIAL_CONTACT to INTEREST_QUALIFICATION."""
    state_machine = ConversationStateMachine("conv_123")

    # Trigger transition to next state
    state_machine.transition_to_next_state()

    assert state_machine.current_state == ConversationState.INTEREST_QUALIFICATION


def test_conversation_state_machine_has_all_seven_states():
    """Test that ConversationState enum has all 7 required states."""
    expected_states = [
        "INITIAL_CONTACT",
        "INTEREST_QUALIFICATION",
        "VALUE_PROPOSITION",
        "OBJECTION_HANDLING",
        "PRICE_NEGOTIATION",
        "CLOSING_ATTEMPT",
        "POST_PURCHASE",
    ]

    actual_states = [state.name for state in ConversationState]

    assert len(actual_states) == 7
    for expected_state in expected_states:
        assert expected_state in actual_states


def test_conversation_state_machine_transitions_through_all_states():
    """Test that state machine can transition through all 7 states sequentially."""
    state_machine = ConversationStateMachine("conv_123")

    expected_sequence = [
        ConversationState.INITIAL_CONTACT,
        ConversationState.INTEREST_QUALIFICATION,
        ConversationState.VALUE_PROPOSITION,
        ConversationState.OBJECTION_HANDLING,
        ConversationState.PRICE_NEGOTIATION,
        ConversationState.CLOSING_ATTEMPT,
        ConversationState.POST_PURCHASE,
    ]

    for expected_state in expected_sequence:
        assert state_machine.current_state == expected_state
        if expected_state != ConversationState.POST_PURCHASE:
            state_machine.transition_to_next_state()


def test_conversation_state_machine_cannot_transition_beyond_final_state():
    """Test that state machine stays in POST_PURCHASE state when trying to transition further."""
    state_machine = ConversationStateMachine("conv_123")

    # Transition to final state
    for _ in range(6):
        state_machine.transition_to_next_state()

    assert state_machine.current_state == ConversationState.POST_PURCHASE

    # Try to transition beyond final state
    state_machine.transition_to_next_state()

    # Should still be in POST_PURCHASE
    assert state_machine.current_state == ConversationState.POST_PURCHASE


def test_conversation_state_machine_can_transition_to_specific_state():
    """Test that state machine can transition directly to a specific state."""
    state_machine = ConversationStateMachine("conv_123")

    # This will fail initially - we need to implement this method
    state_machine.transition_to(ConversationState.PRICE_NEGOTIATION)

    assert state_machine.current_state == ConversationState.PRICE_NEGOTIATION


def test_conversation_state_machine_tracks_state_history():
    """Test that state machine keeps track of previous states."""
    state_machine = ConversationStateMachine("conv_123")

    # Make some transitions
    state_machine.transition_to_next_state()  # INTEREST_QUALIFICATION
    state_machine.transition_to_next_state()  # VALUE_PROPOSITION

    # This will fail initially - we need to implement state history
    expected_history = [
        ConversationState.INITIAL_CONTACT,
        ConversationState.INTEREST_QUALIFICATION,
        ConversationState.VALUE_PROPOSITION,
    ]

    assert state_machine.state_history == expected_history
