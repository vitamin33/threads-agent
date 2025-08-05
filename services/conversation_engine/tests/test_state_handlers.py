"""Tests for individual state handlers."""
import pytest
from datetime import datetime
from services.conversation_engine.states import (
    InitialContactHandler, InterestQualificationHandler, ValuePropositionHandler,
    ObjectionHandlingHandler, PriceNegotiationHandler, ClosingAttemptHandler,
    PostPurchaseHandler, ConversationContext, StateResponse
)


class TestStateHandlers:
    """Test suite for conversation state handlers."""
    
    @pytest.fixture
    def sample_context(self):
        """Create a sample conversation context."""
        return ConversationContext(
            conversation_id="test_conv_123",
            user_id="user_456",
            user_profile={
                "name": "John",
                "communication_style": "casual",
                "interests": ["automation", "efficiency"],
                "pain_points": ["time", "cost"]
            },
            message_history=[],
            current_message="Hi, I saw your post about automation",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_initial_contact_handler_positive_response(self, sample_context):
        """Test initial contact handler with positive response."""
        handler = InitialContactHandler()
        sample_context.current_message = "Yes, I'm interested in learning more!"
        
        response = await handler.handle(sample_context)
        
        assert isinstance(response, StateResponse)
        assert len(response.message) <= 280
        assert response.suggested_next_state == "interest_qualification"
        assert response.confidence_score >= 0.8
        assert not response.requires_human_handoff
    
    @pytest.mark.asyncio
    async def test_initial_contact_handler_negative_response(self, sample_context):
        """Test initial contact handler with negative response."""
        handler = InitialContactHandler()
        sample_context.current_message = "Not interested, please stop messaging me"
        
        response = await handler.handle(sample_context)
        
        assert len(response.message) <= 280
        assert response.suggested_next_state == "initial_contact"  # Stay in same state
        assert response.confidence_score <= 0.6
        assert not response.requires_human_handoff
    
    @pytest.mark.asyncio
    async def test_interest_qualification_clear_pain_point(self, sample_context):
        """Test interest qualification when user expresses clear pain point."""
        handler = InterestQualificationHandler()
        sample_context.current_message = "We spend too much time on manual data entry"
        
        response = await handler.handle(sample_context)
        
        assert response.suggested_next_state == "value_proposition"
        assert response.confidence_score >= 0.9
        assert "time" in response.metadata["pain_points"]
    
    @pytest.mark.asyncio
    async def test_value_proposition_ready_to_buy(self, sample_context):
        """Test value proposition when user shows buying signals."""
        handler = ValuePropositionHandler()
        sample_context.current_message = "This sounds perfect! How do I sign up?"
        
        response = await handler.handle(sample_context)
        
        assert response.suggested_next_state == "closing_attempt"
        assert response.confidence_score >= 0.9
        assert "signup" in response.message.lower() or "start" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_objection_handling_price_concern(self, sample_context):
        """Test objection handling for price concerns."""
        handler = ObjectionHandlingHandler()
        sample_context.current_message = "This seems really expensive for our budget"
        
        response = await handler.handle(sample_context)
        
        assert response.metadata["objection_handled"] == "price"
        assert "invest" in response.message.lower() or "roi" in response.message.lower() or "value" in response.message.lower()
        assert response.confidence_score >= 0.7
    
    @pytest.mark.asyncio
    async def test_price_negotiation_discount_request(self, sample_context):
        """Test price negotiation when user asks for discount."""
        handler = PriceNegotiationHandler()
        sample_context.current_message = "Do you have any discounts or special offers?"
        
        response = await handler.handle(sample_context)
        
        assert "%" in response.message or "off" in response.message.lower() or "discount" in response.message.lower()
        assert response.confidence_score >= 0.8
    
    @pytest.mark.asyncio
    async def test_closing_attempt_purchase_confirmation(self, sample_context):
        """Test closing attempt with purchase confirmation."""
        handler = ClosingAttemptHandler()
        sample_context.current_message = "Yes, let's do it! Sign me up"
        
        response = await handler.handle(sample_context)
        
        assert response.suggested_next_state == "post_purchase"
        assert response.confidence_score == 1.0
        assert "welcome" in response.message.lower() or "🎉" in response.message
    
    @pytest.mark.asyncio
    async def test_post_purchase_support_request(self, sample_context):
        """Test post-purchase handler with support request."""
        handler = PostPurchaseHandler()
        sample_context.current_message = "How do I connect my existing data?"
        sample_context.metadata["days_since_purchase"] = 1
        
        response = await handler.handle(sample_context)
        
        assert response.suggested_next_state == "post_purchase"
        assert "video" in response.message.lower() or "help" in response.message.lower() or "show" in response.message.lower()
        assert not response.requires_human_handoff
    
    @pytest.mark.asyncio
    async def test_escalation_trigger(self, sample_context):
        """Test human handoff escalation."""
        handler = InitialContactHandler()
        sample_context.current_message = "I want to speak to a real person right now!"
        
        response = await handler.handle(sample_context)
        
        assert response.requires_human_handoff
        assert response.confidence_score == 1.0
        assert "connect" in response.message.lower() or "team" in response.message.lower()
    
    def test_message_length_constraint(self):
        """Test that all responses respect 280 character limit."""
        # Test creating response with long message
        with pytest.raises(ValueError):
            StateResponse(
                message="x" * 281,  # 281 characters
                suggested_next_state="test",
                confidence_score=0.5
            )
    
    @pytest.mark.asyncio
    async def test_state_handler_analyze_message(self, sample_context):
        """Test message analysis functionality."""
        handler = InitialContactHandler()
        
        analysis = handler.analyze_message(
            "I'm interested in learning more about your pricing",
            sample_context
        )
        
        assert analysis["sentiment"] == "positive"
        assert analysis["shows_interest"] == True
        assert "pricing" in analysis["keywords_found"]