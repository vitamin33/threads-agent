"""FastAPI application for Variant Performance Dashboard."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from variant_metrics import VariantMetricsAPI
from websocket_handler import VariantDashboardWebSocket
from event_processor import DashboardEventProcessor


# Global instances
websocket_handler = VariantDashboardWebSocket()
metrics_api = VariantMetricsAPI()
event_processor = DashboardEventProcessor(websocket_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Variant Dashboard API...")
    yield
    # Shutdown
    print("Shutting down Variant Dashboard API...")


app = FastAPI(
    title="Variant Performance Dashboard API",
    description="Real-time dashboard for monitoring variant performance",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "variant-dashboard-api"}


@app.get("/api/metrics/{persona_id}")
async def get_metrics(persona_id: str):
    """Get comprehensive metrics for a persona."""
    try:
        metrics = await metrics_api.get_live_metrics(persona_id)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/variants/{persona_id}/active")
async def get_active_variants(persona_id: str):
    """Get active variants with performance data."""
    try:
        variants = await metrics_api.get_active_variants(persona_id)
        return {"variants": variants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/optimization/{persona_id}")
async def get_optimization_suggestions(persona_id: str):
    """Get optimization suggestions for a persona."""
    try:
        suggestions = await metrics_api.get_optimization_suggestions(persona_id)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/dashboard/ws/{persona_id}")
async def websocket_endpoint(websocket: WebSocket, persona_id: str):
    """WebSocket endpoint for real-time dashboard updates."""
    try:
        await websocket_handler.handle_connection(websocket, persona_id)
    except WebSocketDisconnect:
        print(f"Client disconnected from persona {persona_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")


@app.post("/api/events/early-kill")
async def handle_early_kill_event(event_data: dict):
    """Handle early kill events from monitoring system."""
    try:
        await event_processor.handle_early_kill_event(
            event_data["variant_id"], event_data
        )
        return {"status": "processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/performance-update")
async def handle_performance_update(event_data: dict):
    """Handle performance update events."""
    try:
        await event_processor.handle_performance_update(
            event_data["variant_id"], event_data
        )
        return {"status": "processed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
