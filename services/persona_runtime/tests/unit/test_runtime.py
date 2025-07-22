# services/persona_runtime/tests/unit/test_runtime.py
from typing import Any, cast

import pytest

from services.persona_runtime.runtime import build_dag_from_persona


@pytest.mark.asyncio
async def test_dag_produces_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure the DAG returns a formatted draft and injects the emoji."""

    async def fake_llm(model: str, prompt: str, content_type: str = "unknown") -> str:
        return f"resp-{model}"

    async def fake_mod(_text: str) -> bool:
        return True

    monkeypatch.setattr("services.persona_runtime.runtime._llm", fake_llm)
    monkeypatch.setattr("services.persona_runtime.runtime._moderate", fake_mod)

    dag = build_dag_from_persona("ai-jesus")
    assert dag is not None  # satisfy mypy

    res = await cast(Any, dag).ainvoke({"text": "hello"})

    assert res["draft"]["hook"].startswith("🙏")
    assert res["draft"]["body"].startswith("resp-")
