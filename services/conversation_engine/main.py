import uuid
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.conversation_engine.state_machine import ConversationStateMachine, ConversationState

app = FastAPI(title="Conversation Engine", version="1.0.0")

# In-memory storage for conversations (replace with database later)
conversations: Dict[str, ConversationStateMachine] = {}


class TransitionRequest(BaseModel):
    target_state: Optional[str] = None


class ConversationResponse(BaseModel):
    conversation_id: str
    state: str
    state_history: list


class TransitionResponse(BaseModel):
    conversation_id: str
    state: str
    previous_state: str


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "conversation_engine"}


@app.post("/conversations")
async def create_conversation():
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    state_machine = ConversationStateMachine(conversation_id)
    conversations[conversation_id] = state_machine
    
    return {
        "conversation_id": conversation_id,
        "state": state_machine.current_state.value
    }


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation state and history."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    state_machine = conversations[conversation_id]
    
    return {
        "conversation_id": conversation_id,
        "state": state_machine.current_state.value,
        "state_history": [state.value for state in state_machine.state_history]
    }


@app.post("/conversations/{conversation_id}/transition")
async def transition_conversation(conversation_id: str, request: TransitionRequest = None):
    """Transition conversation to next state or specific state."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    state_machine = conversations[conversation_id]
    previous_state = state_machine.current_state
    
    if request and request.target_state:
        # Transition to specific state
        try:
            target_state = ConversationState(request.target_state)
            state_machine.transition_to(target_state)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {request.target_state}")
    else:
        # Transition to next state
        state_machine.transition_to_next_state()
    
    return {
        "conversation_id": conversation_id,
        "state": state_machine.current_state.value,
        "previous_state": previous_state.value
    }