from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from contextlib import asynccontextmanager
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.event_bus.connection.manager import RabbitMQConnectionManager
from services.event_bus.store.postgres_store import PostgreSQLEventStore
from services.event_bus.service import EventBusService
from services.event_bus.models.base import BaseEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
conn_mgr = None
event_store = None
event_bus_service = None


class EventRequest(BaseModel):
    event_type: str
    payload: Dict[str, Any]


class BatchEventRequest(BaseModel):
    events: List[EventRequest]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conn_mgr, event_store, event_bus_service

    # Initialize on startup
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/events"
    )

    conn_mgr = RabbitMQConnectionManager(rabbitmq_url)
    event_store = PostgreSQLEventStore(database_url)

    try:
        await conn_mgr.connect()
        await event_store.initialize_schema()

        # Initialize Event Bus service with batching enabled
        event_bus_service = EventBusService(
            rabbitmq_url=rabbitmq_url,
            postgres_url=database_url,
            batch_size=100,
            batch_timeout=1.0,
            enable_batching=True,
        )
        await event_bus_service.start()

        logger.info("Event Bus initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise

    yield

    # Cleanup on shutdown
    if event_bus_service:
        await event_bus_service.stop()
    if conn_mgr:
        await conn_mgr.disconnect()


app = FastAPI(title="Event Bus Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event-bus"}


@app.get("/ready")
async def readiness_check():
    global conn_mgr
    if conn_mgr and conn_mgr.is_connected:
        return {"status": "ready", "rabbitmq": "connected"}
    return {"status": "not ready", "rabbitmq": "disconnected"}


@app.post("/events")
async def publish_event(event: EventRequest):
    """Publish a single event."""
    global event_bus_service
    if not event_bus_service:
        raise HTTPException(status_code=503, detail="Event Bus not initialized")

    try:
        base_event = BaseEvent(event_type=event.event_type, payload=event.payload)
        success = await event_bus_service.publish_event(base_event)
        if success:
            return {"status": "published", "event_id": base_event.event_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
    except Exception as e:
        logger.error(f"Error publishing event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events/batch")
async def publish_batch_events(request: BatchEventRequest):
    """Publish multiple events in batch."""
    global event_bus_service
    if not event_bus_service:
        raise HTTPException(status_code=503, detail="Event Bus not initialized")

    try:
        events = []
        for event_req in request.events:
            event = BaseEvent(
                event_type=event_req.event_type, payload=event_req.payload
            )
            events.append(event)

        published_count = await event_bus_service.publish_events_batch(events)
        return {
            "status": "published",
            "total": len(events),
            "published": published_count,
            "success_rate": f"{(published_count / len(events) * 100):.1f}%",
        }
    except Exception as e:
        logger.error(f"Error publishing batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get Event Bus metrics."""
    global event_bus_service
    if not event_bus_service:
        raise HTTPException(status_code=503, detail="Event Bus not initialized")

    try:
        metrics = await event_bus_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
