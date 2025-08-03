"""Event processor for dashboard updates from monitoring systems."""

from typing import Dict, Any

from .websocket_handler import VariantDashboardWebSocket


class DashboardEventProcessor:
    """Processes events from monitoring systems and broadcasts to dashboard."""

    def __init__(self, websocket_handler: VariantDashboardWebSocket):
        """Initialize with WebSocket handler."""
        self.websocket_handler = websocket_handler

    async def handle_early_kill_event(
        self, variant_id: str, kill_data: Dict[str, Any]
    ) -> None:
        """Process early kill events for dashboard updates."""
        persona_id = kill_data.get("persona_id")

        if not persona_id:
            return

        update = {
            "event_type": "early_kill",
            "variant_id": variant_id,
            "kill_reason": kill_data.get("reason", "Unknown"),
            "final_er": kill_data.get("final_engagement_rate", 0.0),
            "sample_size": kill_data.get("sample_size", 0),
            "killed_at": kill_data.get("killed_at"),
        }

        await self.websocket_handler.broadcast_variant_update(persona_id, update)

    async def handle_performance_update(
        self, variant_id: str, performance_data: Dict[str, Any]
    ) -> None:
        """Process variant performance updates."""
        persona_id = performance_data.get("persona_id")

        if not persona_id:
            return

        update = {
            "event_type": "performance_update",
            "variant_id": variant_id,
            "current_er": performance_data.get("engagement_rate", 0.0),
            "interaction_count": performance_data.get("interaction_count", 0),
            "view_count": performance_data.get("view_count", 0),
            "updated_at": performance_data.get("updated_at"),
        }

        await self.websocket_handler.broadcast_variant_update(persona_id, update)

    async def handle_pattern_fatigue_alert(
        self, persona_id: str, fatigue_data: Dict[str, Any]
    ) -> None:
        """Process pattern fatigue alerts."""
        update = {
            "event_type": "pattern_fatigue",
            "pattern": fatigue_data.get("pattern"),
            "usage_count": fatigue_data.get("usage_count", 0),
            "fatigue_score": fatigue_data.get("fatigue_score", 0.0),
            "recommendation": fatigue_data.get("recommendation", "Reduce usage"),
        }

        await self.websocket_handler.broadcast_variant_update(persona_id, update)

    async def handle_optimization_alert(
        self, persona_id: str, optimization_data: Dict[str, Any]
    ) -> None:
        """Process optimization alerts."""
        update = {
            "event_type": "optimization_alert",
            "alert_type": optimization_data.get("type"),
            "title": optimization_data.get("title"),
            "description": optimization_data.get("description"),
            "action": optimization_data.get("action"),
            "priority": optimization_data.get("priority", "medium"),
        }

        await self.websocket_handler.broadcast_variant_update(persona_id, update)
