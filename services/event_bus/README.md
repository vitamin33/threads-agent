# Event Bus Service

High-performance event-driven microservice for the Threads-Agent Stack, providing reliable message publishing, subscription, and persistence capabilities.

## Quick Start

```bash
# Install dependencies
cd services/event_bus
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run locally
uvicorn api:app --reload

# Run tests
python -m pytest tests/ -v

# Run integration tests (requires infrastructure)
python test_cluster_integration.py
```

## Features

- **High Performance**: 1000+ messages/second throughput
- **Reliable Delivery**: RabbitMQ with persistence and acknowledgments
- **Event Persistence**: PostgreSQL storage with replay capabilities
- **Circuit Breakers**: Automatic retry with exponential backoff
- **Health Monitoring**: Kubernetes-ready health and readiness probes
- **Type Safety**: Pydantic models with validation
- **Async Design**: Built on asyncio for high concurrency

## Architecture

```
services/event_bus/
├── api.py                    # FastAPI service entry point
├── connection/
│   └── manager.py           # RabbitMQ connection management
├── models/
│   └── base.py             # Event data models
├── publishers/
│   └── publisher.py        # Event publishing logic
├── subscribers/
│   └── subscriber.py       # Event subscription handlers
├── store/
│   └── postgres_store.py   # Event persistence layer
└── tests/                  # Unit and integration tests
```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check with dependency status

## Configuration

Environment variables:
- `RABBITMQ_URL` - RabbitMQ connection URL (default: amqp://guest:guest@localhost:5672/)
- `DATABASE_URL` - PostgreSQL connection URL (default: postgresql://postgres:postgres@localhost:5432/events)
- `LOG_LEVEL` - Logging level (default: INFO)

## Integration

### Publishing Events

```python
from event_bus.publishers import EventPublisher
from event_bus.models import BaseEvent

# Create publisher
publisher = EventPublisher(connection_manager)

# Publish event
event = BaseEvent(
    event_type="user.created",
    payload={"user_id": "123", "email": "user@example.com"}
)
await publisher.publish_event(event, exchange="events_exchange")
```

### Subscribing to Events

```python
from event_bus.subscribers import EventSubscriber

# Create subscriber
subscriber = EventSubscriber(connection_manager)

# Define handler
async def handle_user_created(event):
    print(f"New user: {event.payload['user_id']}")

# Subscribe
await subscriber.subscribe(
    exchange="events_exchange",
    routing_key="user.created",
    handler=handle_user_created
)
```

## Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests (requires Docker)
docker-compose up -d
python -m pytest tests/integration/ -v

# Full cluster test
python test_cluster_integration.py
```

## Performance

- **Throughput**: 1000+ messages/second
- **Latency**: <10ms p95 for event publishing
- **Storage**: 100+ events/second write throughput
- **Concurrency**: Handles 50+ concurrent publishers

## Documentation

- [Technical Documentation](./TECHNICAL_DOCUMENTATION.md) - Comprehensive technical guide
- [API Reference](./docs/api.md) - Detailed API documentation
- [Integration Guide](./docs/integration.md) - Service integration examples

## License

Part of the Threads-Agent Stack - See repository root for license information.