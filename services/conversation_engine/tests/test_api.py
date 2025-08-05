import pytest
from fastapi.testclient import TestClient
from services.conversation_engine.main import app

client = TestClient(app)


def test_create_conversation_returns_conversation_id():
    """Test creating a new conversation returns a conversation ID."""
    response = client.post("/conversations")
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert data["state"] == "initial_contact"


def test_get_conversation_state_returns_current_state():
    """Test getting conversation state returns current state."""
    # First create a conversation
    create_response = client.post("/conversations")
    conversation_id = create_response.json()["conversation_id"]
    
    # Get the conversation state
    response = client.get(f"/conversations/{conversation_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_id
    assert data["state"] == "initial_contact"
    assert data["state_history"] == ["initial_contact"]


def test_transition_conversation_to_next_state():
    """Test transitioning conversation to next state."""
    # Create conversation
    create_response = client.post("/conversations")
    conversation_id = create_response.json()["conversation_id"]
    
    # Transition to next state
    response = client.post(f"/conversations/{conversation_id}/transition")
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_id
    assert data["state"] == "interest_qualification"
    assert data["previous_state"] == "initial_contact"


def test_transition_conversation_to_specific_state():
    """Test transitioning conversation to a specific state."""
    # Create conversation
    create_response = client.post("/conversations")
    conversation_id = create_response.json()["conversation_id"]
    
    # Transition to specific state
    response = client.post(
        f"/conversations/{conversation_id}/transition", 
        json={"target_state": "price_negotiation"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == conversation_id
    assert data["state"] == "price_negotiation"


def test_get_nonexistent_conversation_returns_404():
    """Test getting a nonexistent conversation returns 404."""
    response = client.get("/conversations/nonexistent_id")
    
    assert response.status_code == 404


def test_health_endpoint_returns_ok():
    """Test health endpoint returns OK."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "conversation_engine"}