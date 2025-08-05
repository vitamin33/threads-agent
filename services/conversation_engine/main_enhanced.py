"""Enhanced FastAPI application for conversation engine service."""
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import time
import asyncio
import os

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import redis
import httpx

from services.conversation_engine.state_machine import ConversationStateMachine, ConversationState
from services.conversation_engine.memory import ConversationMemorySystem, ConversationMemory
from services.conversation_engine.personalization import PersonalizationEngine, PersonalizationRequest
from services.conversation_engine.states import (
    InitialContactHandler, InterestQualificationHandler, ValuePropositionHandler,
    ObjectionHandlingHandler, PriceNegotiationHandler, ClosingAttemptHandler,
    PostPurchaseHandler, ConversationContext
)

app = FastAPI(title="Conversation Engine", version="2.0.0")

# Initialize components
memory_system = ConversationMemorySystem()
personalization_engine = PersonalizationEngine()

# State handlers mapping
state_handlers = {
    ConversationState.INITIAL_CONTACT: InitialContactHandler(),
    ConversationState.INTEREST_QUALIFICATION: InterestQualificationHandler(),
    ConversationState.VALUE_PROPOSITION: ValuePropositionHandler(),
    ConversationState.OBJECTION_HANDLING: ObjectionHandlingHandler(),
    ConversationState.PRICE_NEGOTIATION: PriceNegotiationHandler(),
    ConversationState.CLOSING_ATTEMPT: ClosingAttemptHandler(),
    ConversationState.POST_PURCHASE: PostPurchaseHandler(),
}

# Redis client for real-time features
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True
)


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""
    user_id: str
    user_profile: Optional[Dict[str, Any]] = {}
    initial_message: Optional[str] = ""


class MessageRequest(BaseModel):
    """Request model for processing a message."""
    message: str
    metadata: Optional[Dict[str, Any]] = {}


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    conversation_id: str
    current_state: str
    state_history: List[str]
    user_id: str
    conversion_probability: float
    last_interaction: str


class MessageResponse(BaseModel):
    """Response model for message processing."""
    response: str
    current_state: str
    next_state: Optional[str]
    confidence_score: float
    requires_human_handoff: bool
    response_time_ms: int


class ConversationAnalytics(BaseModel):
    """Analytics data for a conversation."""
    conversation_id: str
    total_turns: int
    avg_response_time_ms: float
    state_transitions: List[tuple]
    repeated_objections: List[str]
    conversion_journey_length: int
    stuck_in_state: Optional[str]


@app.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreate):
    """Create a new conversation with initial setup."""
    conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
    
    # Create memory object
    memory = ConversationMemory(
        conversation_id=conversation_id,
        user_id=request.user_id,
        current_state=ConversationState.INITIAL_CONTACT.value,
        state_history=[ConversationState.INITIAL_CONTACT.value],
        user_profile=request.user_profile,
        conversation_turns=[],
        metadata={"created_at": datetime.utcnow().isoformat()},
        conversion_probability=0.0,
        last_interaction=datetime.utcnow()
    )
    
    # Save to memory system
    await memory_system.save_conversation(memory)
    
    # Process initial message if provided
    if request.initial_message:
        # Process the message async
        asyncio.create_task(
            process_message_async(conversation_id, request.initial_message, {})
        )
    
    return ConversationResponse(
        conversation_id=conversation_id,
        current_state=memory.current_state,
        state_history=memory.state_history,
        user_id=memory.user_id,
        conversion_probability=memory.conversion_probability,
        last_interaction=memory.last_interaction.isoformat()
    )


@app.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get conversation state and details."""
    memory = await memory_system.get_conversation(conversation_id)
    
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationResponse(
        conversation_id=memory.conversation_id,
        current_state=memory.current_state,
        state_history=memory.state_history,
        user_id=memory.user_id,
        conversion_probability=memory.conversion_probability,
        last_interaction=memory.last_interaction.isoformat()
    )


@app.post("/conversations/{conversation_id}/message", response_model=MessageResponse)
async def process_message(conversation_id: str, request: MessageRequest):
    """Process a user message and generate personalized response."""
    start_time = time.time()
    
    # Get conversation from memory
    memory = await memory_system.get_conversation(conversation_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Create conversation context
    context = ConversationContext(
        conversation_id=conversation_id,
        user_id=memory.user_id,
        user_profile=memory.user_profile,
        message_history=memory.conversation_turns,
        current_message=request.message,
        metadata=request.metadata or {},
        created_at=datetime.fromisoformat(memory.metadata.get("created_at", datetime.utcnow().isoformat())),
        updated_at=datetime.utcnow()
    )
    
    # Get current state handler
    current_state = ConversationState(memory.current_state)
    handler = state_handlers[current_state]
    
    # Process message with handler
    state_response = await handler.handle(context)
    
    # Personalize the response
    personalization_request = PersonalizationRequest(
        state=memory.current_state,
        user_message=request.message,
        conversation_history=memory.conversation_turns[-5:],  # Last 5 turns
        user_profile=memory.user_profile,
        suggested_response=state_response.message
    )
    
    personalized_message = await personalization_engine.generate_response(personalization_request)
    
    # Update state if suggested
    new_state = memory.current_state
    if state_response.suggested_next_state and not state_response.requires_human_handoff:
        new_state = state_response.suggested_next_state
        memory.current_state = new_state
        memory.state_history.append(new_state)
    
    # Calculate response time
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Save conversation turn
    await memory_system.add_conversation_turn(
        conversation_id=conversation_id,
        user_message=request.message,
        bot_message=personalized_message,
        state_before=current_state.value,
        state_after=new_state,
        intent_analysis=handler.analyze_message(request.message, context),
        response_time_ms=response_time_ms
    )
    
    # Update conversation memory
    memory.last_interaction = datetime.utcnow()
    memory.conversion_probability = state_response.confidence_score
    await memory_system.save_conversation(memory)
    
    # Publish to Redis for real-time updates
    redis_client.publish(
        f"conversation:{conversation_id}",
        personalized_message
    )
    
    return MessageResponse(
        response=personalized_message,
        current_state=memory.current_state,
        next_state=state_response.suggested_next_state,
        confidence_score=state_response.confidence_score,
        requires_human_handoff=state_response.requires_human_handoff,
        response_time_ms=response_time_ms
    )


@app.get("/conversations/{conversation_id}/analytics", response_model=ConversationAnalytics)
async def get_conversation_analytics(conversation_id: str):
    """Get detailed analytics for a conversation."""
    analytics = memory_system.analyze_conversation_patterns(conversation_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationAnalytics(
        conversation_id=conversation_id,
        **analytics
    )


@app.get("/users/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: str):
    """Get all conversations for a specific user."""
    conversations = await memory_system.get_user_conversations(user_id)
    
    return [
        ConversationResponse(
            conversation_id=conv.conversation_id,
            current_state=conv.current_state,
            state_history=conv.state_history,
            user_id=conv.user_id,
            conversion_probability=conv.conversion_probability,
            last_interaction=conv.last_interaction.isoformat()
        )
        for conv in conversations
    ]


@app.get("/conversations/active", response_model=List[str])
async def get_active_conversations(hours: int = 24):
    """Get list of active conversation IDs within specified hours."""
    return await memory_system.get_active_conversations(hours)


@app.post("/conversations/{conversation_id}/handoff")
async def handoff_to_human(conversation_id: str):
    """Mark conversation for human handoff."""
    memory = await memory_system.get_conversation(conversation_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update metadata to indicate handoff
    memory.metadata["human_handoff"] = True
    memory.metadata["handoff_time"] = datetime.utcnow().isoformat()
    await memory_system.save_conversation(memory)
    
    # Notify human agents (in production, would integrate with support system)
    # For now, just publish to Redis
    redis_client.publish(
        "human_handoff",
        f"{conversation_id}:{memory.user_id}"
    )
    
    return {"status": "handoff_initiated", "conversation_id": conversation_id}


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check Redis
        redis_client.ping()
        redis_healthy = True
    except:
        redis_healthy = False
    
    return {
        "status": "healthy" if redis_healthy else "degraded",
        "service": "conversation_engine",
        "version": "2.0.0",
        "components": {
            "redis": redis_healthy,
            "memory_system": True,
            "personalization": True,
            "handlers": len(state_handlers)
        }
    }


@app.get("/metrics")
async def get_metrics():
    """Get service metrics for monitoring."""
    active_1h = await memory_system.get_active_conversations(1)
    active_24h = await memory_system.get_active_conversations(24)
    
    return {
        "active_conversations_1h": len(active_1h),
        "active_conversations_24h": len(active_24h),
        "handlers_loaded": len(state_handlers),
        "states_available": [state.value for state in ConversationState],
        "service": "conversation_engine"
    }


async def process_message_async(conversation_id: str, message: str, metadata: Dict[str, Any]):
    """Process message asynchronously (for initial messages)."""
    try:
        # Simulate API call
        async with httpx.AsyncClient() as client:
            await client.post(
                f"http://localhost:8080/conversations/{conversation_id}/message",
                json={"message": message, "metadata": metadata}
            )
    except Exception as e:
        print(f"Error processing async message: {e}")