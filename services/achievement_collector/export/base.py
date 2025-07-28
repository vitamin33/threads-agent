"""
Base exporter interface for all export formats.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..db.models import Achievement


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    @abstractmethod
    async def export(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Export achievements in the specific format.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters (date range, categories, etc.)

        Returns:
            Export result (format-specific)
        """
        pass

    def get_achievements(
        self,
        db: Session,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Achievement]:
        """
        Get filtered achievements from database.

        Args:
            db: Database session
            user_id: Optional user ID filter
            filters: Additional filters

        Returns:
            List of achievements
        """
        query = db.query(Achievement)

        if user_id:
            query = query.filter(Achievement.user_id == user_id)

        if filters:
            # Apply date range filter
            if "start_date" in filters:
                query = query.filter(Achievement.completed_at >= filters["start_date"])
            if "end_date" in filters:
                query = query.filter(Achievement.completed_at <= filters["end_date"])

            # Apply category filter
            if "categories" in filters:
                query = query.filter(Achievement.category.in_(filters["categories"]))

            # Apply portfolio_ready filter
            if "portfolio_ready" in filters:
                query = query.filter(
                    Achievement.portfolio_ready == filters["portfolio_ready"]
                )

        return query.order_by(Achievement.completed_at.desc()).all()
