from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connection.manager import RabbitMQConnectionManager
from store.postgres_store import PostgreSQLEventStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
conn_mgr = None
event_store = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global conn_mgr, event_store
    
    # Initialize on startup
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/events")
    
    conn_mgr = RabbitMQConnectionManager(rabbitmq_url)
    event_store = PostgreSQLEventStore(database_url)
    
    try:
        await conn_mgr.connect()
        await event_store.initialize_schema()
        logger.info("Event Bus initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
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