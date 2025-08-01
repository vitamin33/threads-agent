"""WebSocket handler for real-time dashboard updates."""

from datetime import datetime
from typing import Dict, Set, Any
import json
from fastapi import WebSocket

from variant_metrics import VariantMetricsAPI


class VariantDashboardWebSocket:
    """Handles WebSocket connections for real-time dashboard updates."""
    
    def __init__(self):
        """Initialize WebSocket handler."""
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.metrics_api = VariantMetricsAPI()
    
    async def handle_connection(self, websocket: WebSocket, persona_id: str):
        """Handle new dashboard WebSocket connection."""
        await websocket.accept()
        
        # Add connection to persona's set
        if persona_id not in self.connections:
            self.connections[persona_id] = set()
        
        self.connections[persona_id].add(websocket)
        
        try:
            # Send initial data
            await self.send_initial_data(websocket, persona_id)
            
            # Keep connection alive and handle messages
            while True:
                try:
                    message = await websocket.receive_text()
                    await self.handle_message(websocket, persona_id, message)
                except Exception:
                    break
                    
        finally:
            # Clean up connection
            self.connections[persona_id].discard(websocket)
            if not self.connections[persona_id]:
                del self.connections[persona_id]
    
    async def send_initial_data(self, websocket: WebSocket, persona_id: str):
        """Send initial dashboard data to newly connected client."""
        initial_data = await self.metrics_api.get_live_metrics(persona_id)
        await websocket.send_json({
            "type": "initial_data",
            "data": initial_data
        })
    
    async def handle_message(self, websocket: WebSocket, persona_id: str, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "refresh":
                # Client requests fresh data
                await self.send_initial_data(websocket, persona_id)
            elif message_type == "ping":
                # Heartbeat
                await websocket.send_json({"type": "pong"})
                
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid JSON"
            })
    
    async def broadcast_variant_update(self, persona_id: str, update_data: Dict[str, Any]):
        """Broadcast variant performance updates to connected dashboards."""
        if persona_id not in self.connections:
            return
        
        message = {
            "type": "variant_update",
            "timestamp": datetime.now().isoformat(),
            "data": update_data
        }
        
        # Broadcast to all connected clients for this persona
        disconnected = set()
        for websocket in self.connections[persona_id].copy():
            try:
                await websocket.send_json(message)
            except Exception:
                # Mark for removal if disconnected
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.connections[persona_id].discard(websocket)
    
    async def broadcast_early_kill(self, persona_id: str, kill_data: Dict[str, Any]):
        """Broadcast early kill event."""
        update = {
            "event_type": "early_kill",
            "variant_id": kill_data.get("variant_id"),
            "kill_reason": kill_data.get("reason"),
            "final_er": kill_data.get("final_engagement_rate"),
            "sample_size": kill_data.get("sample_size")
        }
        
        await self.broadcast_variant_update(persona_id, update)
    
    async def broadcast_performance_update(self, persona_id: str, performance_data: Dict[str, Any]):
        """Broadcast variant performance update."""
        update = {
            "event_type": "performance_update",
            "variant_id": performance_data.get("variant_id"),
            "current_er": performance_data.get("engagement_rate"),
            "interaction_count": performance_data.get("interaction_count")
        }
        
        await self.broadcast_variant_update(persona_id, update)