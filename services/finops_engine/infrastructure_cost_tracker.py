"""
Infrastructure Cost Tracker - K8s resources, databases, and monitoring cost tracking.

Minimal implementation to make our TDD tests pass.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional


class InfrastructureCostTracker:
    """
    Tracks infrastructure costs including K8s resources, databases, and monitoring.

    Minimal implementation following TDD principles.
    """

    # Default pricing (estimated cloud provider costs)
    DEFAULT_PRICING = {
        "kubernetes": {
            "cpu_hour_cost": 0.048,  # $0.048 per CPU hour
            "memory_gb_hour_cost": 0.012,  # $0.012 per GB memory hour
            "storage_gb_month_cost": 0.10,  # $0.10 per GB storage per month
        },
        "postgresql": {
            "query_cost_per_1k": 0.0001,  # $0.0001 per 1K queries
            "storage_gb_month_cost": 0.15,  # $0.15 per GB storage per month
        },
        "qdrant": {
            "query_cost_per_1k": 0.0002,  # $0.0002 per 1K vector queries
            "storage_gb_month_cost": 0.25,  # $0.25 per GB vector storage per month
        },
    }

    def __init__(self, pricing_config: Optional[Dict[str, Dict[str, float]]] = None):
        """Initialize the Infrastructure cost tracker with pricing configuration."""
        self.pricing_config = pricing_config or self.DEFAULT_PRICING

    def calculate_resource_cost(self, resource_type: str, **kwargs) -> float:
        """Calculate cost for a resource based on type and usage parameters."""
        if resource_type == "kubernetes":
            return self._calculate_k8s_cost(**kwargs)
        elif resource_type == "postgresql":
            return self._calculate_db_cost("postgresql", **kwargs)
        elif resource_type == "qdrant":
            return self._calculate_db_cost("qdrant", **kwargs)
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    def _calculate_k8s_cost(
        self, cpu_cores: float, memory_gb: float, duration_minutes: int
    ) -> float:
        """Calculate K8s resource cost based on CPU, memory, and duration."""
        pricing = self.pricing_config["kubernetes"]
        duration_hours = duration_minutes / 60.0

        cpu_cost = cpu_cores * pricing["cpu_hour_cost"] * duration_hours
        memory_cost = memory_gb * pricing["memory_gb_hour_cost"] * duration_hours

        return cpu_cost + memory_cost

    def _calculate_db_cost(self, db_type: str, query_count: int) -> float:
        """Calculate database operation cost based on query count."""
        if db_type not in self.pricing_config:
            raise ValueError(f"Unknown database type: {db_type}")

        pricing = self.pricing_config[db_type]
        return (query_count / 1000) * pricing["query_cost_per_1k"]

    def track_k8s_resource_usage(
        self,
        resource_type: str,
        resource_name: str,
        service: str,
        cpu_cores: float,
        memory_gb: float,
        duration_minutes: int,
        operation: str,
    ) -> Dict[str, Any]:
        """Track K8s resource usage and return a cost event."""
        cost_amount = self._calculate_k8s_cost(cpu_cores, memory_gb, duration_minutes)

        cost_event = {
            "cost_amount": cost_amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resource_type": resource_type,
            "resource_name": resource_name,
            "service": service,
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "duration_minutes": duration_minutes,
            "operation": operation,
            "cost_type": "kubernetes",
        }

        return cost_event

    def track_database_operation(
        self,
        db_type: str,
        operation: str,
        query_count: int,
        table: str,
        persona_id: str,
    ) -> Dict[str, Any]:
        """Track database operation and return a cost event."""
        cost_amount = self._calculate_db_cost(db_type, query_count)

        cost_event = {
            "cost_amount": cost_amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "db_type": db_type,
            "operation": operation,
            "query_count": query_count,
            "table": table,
            "persona_id": persona_id,
            "cost_type": "database",
        }

        return cost_event

    def track_vector_db_operation(
        self, operation: str, query_count: int, collection: str, persona_id: str
    ) -> Dict[str, Any]:
        """Track vector database operation and return a cost event."""
        cost_amount = self._calculate_db_cost("qdrant", query_count)

        cost_event = {
            "cost_amount": cost_amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "query_count": query_count,
            "collection": collection,
            "persona_id": persona_id,
            "cost_type": "vector_db",
        }

        return cost_event
