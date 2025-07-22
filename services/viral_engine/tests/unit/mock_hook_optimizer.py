# services/viral_engine/tests/unit/mock_hook_optimizer.py
from __future__ import annotations

from typing import Any, Dict


class MockHookOptimizer:
    """Mock HookOptimizer for testing purposes"""

    async def optimize_hook(self, persona_id: str, content: str) -> Dict[str, Any]:
        """Mock hook optimization"""
        return {
            "optimized_hook": f"🚀 {content}",
            "pattern": {"name": "emoji_hook"},
            "predicted_ctr_boost": 0.15,
        }
