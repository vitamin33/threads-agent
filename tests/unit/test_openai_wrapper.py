# tests/unit/test_openai_wrapper.py
from types import SimpleNamespace

import fakeredis
import pytest
from openai.types import CompletionUsage

import services.common.openai_wrapper as ow
from services.common.openai_wrapper import track_cost


@pytest.mark.asyncio
async def test_track_cost_pushes_row(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_redis = fakeredis.FakeRedis()
    monkeypatch.setattr(ow, "_redis", lambda: fake_redis)
    # bypass tenacity retry wrapper to keep test fast
    monkeypatch.setattr("services.common.openai_wrapper._retry", lambda fn: fn)

    # 👉 minimal fake OpenAI response
    fake_resp = SimpleNamespace(
        model="gpt-4o",
        usage=CompletionUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
    )

    async def fake_call() -> object:  # could return anything
        return fake_resp

    wrapped = track_cost(persona="unit-bot", task="test")(fake_call)
    await wrapped()

    assert fake_redis.llen("llm_costs") == 1
