# Event Bus Integration Tests

This directory contains comprehensive integration tests for the Event-Driven Architecture implementation in `services/event_bus/`. These tests verify that all components work together correctly in realistic scenarios.

## Test Structure

### Core Test Files

1. **`test_end_to_end_flow.py`** - Full Event Flow Testing
   - Single event complete flow (publish → store → consume → handle)
   - Multiple events sequential processing
   - Event flow with filtering based on event type
   - Concurrent publishing and consuming under load
   - Event flow with detailed persistence verification

2. **`test_event_replay.py`** - Event Store Replay Functionality
   - Basic event replay with ordering guarantees
   - Time-based filtering (start_time, end_time, both)
   - Event type filtering
   - Combined time and type filtering
   - Result limiting and pagination
   - Complex payload integrity during replay
   - Concurrent store and replay operations

3. **`test_error_handling.py`** - Error Scenarios and Dead Letter Queue
   - Handler failure preventing message acknowledgment
   - Partial handler failures with multiple handlers
   - Publisher retry logic on connection failures
   - Event store failure resilience
   - Malformed message handling
   - Connection recovery scenarios
   - Dead letter queue simulation
   - Exception propagation and logging

4. **`test_multiple_subscribers.py`** - Multiple Handler Scenarios
   - Multiple handlers for same event type
   - Multiple subscribers with load balancing
   - Selective event handling by different subscribers
   - Handler failure isolation between subscribers
   - Concurrent handler execution timing

5. **`test_event_ordering.py`** - Message Ordering Guarantees
   - FIFO ordering with single consumer
   - Timestamp-based ordering preservation
   - Ordering with variable processing delays
   - Ordering under high message load
   - Ordering across reconnections
   - Ordering with multiple routing keys

### Test Infrastructure

- **`conftest.py`** - Comprehensive fixture definitions
  - RabbitMQ and PostgreSQL containers using testcontainers
  - Event bus component fixtures (publisher, subscriber, event store)
  - Test utilities (event capture, ordering verification)
  - Mock fixtures for error simulation

## Test Features

### Container-Based Testing
- Uses `testcontainers` for isolated RabbitMQ and PostgreSQL instances
- Automatic cleanup after test sessions
- Realistic environment simulation

### Event Capture and Analysis
- `EventCapture` utility class for tracking events and handler calls
- Message ordering verification utilities
- Processing time measurement and analysis

### Error Simulation
- Mock connection failures
- Handler exception scenarios
- Database unavailability simulation
- Malformed message injection

### Comprehensive Scenarios
- **Load Testing**: High-volume message processing (up to 100 events)
- **Concurrency Testing**: Multiple publishers, subscribers, and handlers
- **Resilience Testing**: Connection failures, handler errors, recovery
- **Ordering Testing**: FIFO guarantees, timestamp preservation
- **Integration Testing**: Full system integration with persistence

## Running the Tests

### Prerequisites

Install additional dependencies:
```bash
pip install testcontainers requests
```

Ensure Docker is running for container-based tests.

### Execution

Run all integration tests:
```bash
pytest tests/integration/ -v
```

Run specific test categories:
```bash
# End-to-end flow tests
pytest tests/integration/test_end_to_end_flow.py -v

# Event replay tests
pytest tests/integration/test_event_replay.py -v

# Error handling tests
pytest tests/integration/test_error_handling.py -v

# Multiple subscribers tests
pytest tests/integration/test_multiple_subscribers.py -v

# Event ordering tests
pytest tests/integration/test_event_ordering.py -v
```

Run with coverage:
```bash
pytest tests/integration/ --cov=services.event_bus --cov-report=html
```

### Test Markers

Tests use standard pytest-asyncio markers:
- `@pytest.mark.asyncio` - Async test functions
- Container fixtures automatically handle setup/teardown

## Test Coverage

### Component Coverage
- ✅ **EventPublisher**: Publishing, retries, connection handling
- ✅ **EventSubscriber**: Consumption, handler registration, error handling
- ✅ **PostgreSQLEventStore**: Storage, retrieval, replay functionality
- ✅ **RabbitMQConnectionManager**: Connection management, reconnection
- ✅ **BaseEvent**: Event model integrity and serialization

### Scenario Coverage
- ✅ **Happy Path**: Normal operation end-to-end
- ✅ **Error Handling**: Various failure modes and recovery
- ✅ **Load Testing**: High-volume message processing
- ✅ **Concurrency**: Multiple publishers/subscribers
- ✅ **Ordering**: Message ordering guarantees
- ✅ **Persistence**: Event storage and replay
- ✅ **Filtering**: Event type and time-based filtering

### Edge Cases
- ✅ Connection failures and recovery
- ✅ Handler exceptions and error propagation
- ✅ Malformed message handling
- ✅ Database unavailability
- ✅ High-load scenarios
- ✅ Complex payload integrity
- ✅ Timestamp-based operations

## Key Utilities

### EventCapture Class
```python
capture = EventCapture()
handler = capture.create_handler("test_handler", should_fail=False)
# Access captured events: capture.events
# Access handler call counts: capture.handler_calls
# Access errors: capture.errors
```

### Ordering Verification
```python
def verify_ordering(received_events, expected_order):
    # Returns True if events received in expected order
```

### Async Timeout Helper
```python
await async_timeout(some_coroutine(), timeout=5.0)
```

## Test Philosophy

These integration tests follow the principle of testing component interactions in realistic scenarios while maintaining test isolation and repeatability. They complement the existing unit tests by verifying that the event bus system works correctly when all components are integrated together.

The tests are designed to:
- **Catch Integration Issues**: Problems that only appear when components interact
- **Verify End-to-End Flows**: Complete workflows from publishing to handling
- **Test Error Scenarios**: Real-world failure modes and recovery
- **Validate Performance**: System behavior under load
- **Ensure Correctness**: Message ordering and integrity guarantees

## Maintenance

When adding new features to the event bus:
1. Add corresponding integration tests
2. Update existing tests if interfaces change
3. Maintain test isolation and cleanup
4. Document new test utilities in this README