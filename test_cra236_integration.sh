#!/bin/bash
# CRA-236 Integration Test Script
# Tests the conversation engine deployed on local k3d cluster

set -e

echo "🚀 Starting CRA-236 Conversation Engine Integration Tests"
echo "📅 Test started at: $(date)"
echo

# Start port forwarding
echo "🔧 Setting up port forwarding..."
kubectl port-forward svc/conversation-engine 8082:8080 &
PORT_FORWARD_PID=$!

# Give port forwarding time to establish
sleep 3

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up port forwarding..."
    kill $PORT_FORWARD_PID 2>/dev/null || true
    wait $PORT_FORWARD_PID 2>/dev/null || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Test counters
TESTS_PASSED=0
TOTAL_TESTS=4

# Test 1: Health endpoint
echo "Test 1: Health endpoint"
if curl -s -f http://localhost:8082/health > /dev/null; then
    HEALTH_RESPONSE=$(curl -s http://localhost:8082/health)
    if echo "$HEALTH_RESPONSE" | grep -q "ok"; then
        echo "✅ Health endpoint test passed"
        ((TESTS_PASSED++))
    else
        echo "❌ Health endpoint returned wrong response: $HEALTH_RESPONSE"
    fi
else
    echo "❌ Health endpoint test failed - could not connect"
fi

# Test 2: Conversation creation
echo "Test 2: Conversation creation"
CONVERSATION_RESPONSE=$(curl -s -X POST http://localhost:8082/conversations \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user_integration_123", "initial_message": "Hi, I am interested in your AI automation services"}')

if echo "$CONVERSATION_RESPONSE" | grep -q "conversation_id"; then
    CONVERSATION_ID=$(echo "$CONVERSATION_RESPONSE" | grep -o '"conversation_id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Conversation creation test passed - ID: $CONVERSATION_ID"
    ((TESTS_PASSED++))
    
    # Test 3: Conversation transition
    echo "Test 3: Conversation state transition"
    TRANSITION_RESPONSE=$(curl -s -X POST "http://localhost:8082/conversations/$CONVERSATION_ID/transition" \
        -H "Content-Type: application/json" \
        -d '{"user_message": "I want to know more about pricing and implementation timeline", "user_name": "John Doe"}')
    
    if echo "$TRANSITION_RESPONSE" | grep -q "previous_state"; then
        echo "✅ Conversation transition test passed"
        echo "   Response: $TRANSITION_RESPONSE"
        ((TESTS_PASSED++))
    else
        echo "❌ Conversation transition test failed"
        echo "   Response: $TRANSITION_RESPONSE"
    fi
    
    # Test 4: Conversation retrieval
    echo "Test 4: Conversation retrieval"
    RETRIEVAL_RESPONSE=$(curl -s "http://localhost:8082/conversations/$CONVERSATION_ID")
    
    if echo "$RETRIEVAL_RESPONSE" | grep -q "state_history"; then
        echo "✅ Conversation retrieval test passed"
        ((TESTS_PASSED++))
    else
        echo "❌ Conversation retrieval test failed"
        echo "   Response: $RETRIEVAL_RESPONSE"
    fi
    
else
    echo "❌ Conversation creation test failed"
    echo "   Response: $CONVERSATION_RESPONSE"
fi

echo
echo "📊 Test Results: $TESTS_PASSED/$TOTAL_TESTS tests passed"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    echo "🎉 All CRA-236 integration tests passed!"
    echo "✅ Conversation Engine is working correctly on k3d cluster"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi