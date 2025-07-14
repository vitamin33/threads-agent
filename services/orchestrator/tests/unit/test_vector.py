# services/orchestrator/tests/unit/test_vector.py
import importlib
import os
import time
import uuid

# regular, data-only imports first
import numpy as np
from qdrant_client.models import PointStruct

# 1️⃣ configure test backend *before* the vector module is imported
os.environ["QDRANT_URL"] = ":memory:"

import services.orchestrator.vector as vector  # noqa: E402  (allowed after top imports)

# 2️⃣ reload so vector.py picks up the env-var
importlib.reload(vector)

# alias helpers from the reloaded module
ensure_posts_collection = vector.ensure_posts_collection
get_client = vector.get_client


def test_insert_and_search() -> None:
    """Smoke-test in-memory Qdrant insert → search."""
    ensure_posts_collection()
    client = get_client()

    vec = np.random.rand(128).tolist()
    pid = str(uuid.uuid4())

    client.upsert("posts_ai-jesus", [PointStruct(id=pid, vector=vec)])
    time.sleep(0.05)  # index settle

    hit = client.search("posts_ai-jesus", vec, limit=1)[0]
    assert hit.id == pid and hit.score >= 0.9
