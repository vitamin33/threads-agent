"""Pytest configuration and fixtures."""

import asyncio
import tempfile
import pytest
from unittest.mock import Mock, AsyncMock
import numpy as np

# Configure asyncio for tests
pytest_plugins = ["pytest_asyncio"]

# Set asyncio mode for pytest-asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc1",
            "content": "This is a test document about machine learning and artificial intelligence.",
            "metadata": {"source": "test1.txt", "category": "tech"},
        },
        {
            "id": "doc2",
            "content": "Natural language processing is a branch of AI that deals with human language.",
            "metadata": {"source": "test2.txt", "category": "tech"},
        },
        {
            "id": "doc3",
            "content": "Deep learning uses neural networks to model complex patterns in data.",
            "metadata": {"source": "test3.txt", "category": "tech"},
        },
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [np.random.rand(1536).tolist() for _ in range(3)]


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    mock = Mock()
    mock.collection_exists.return_value = True
    mock.get_collection.return_value = Mock(
        status="green",
        vectors_count=100,
        points_count=100,
        config=Mock(params=Mock(vectors=Mock(size=1536))),
    )
    mock.upsert.return_value = Mock()
    mock.search.return_value = [
        Mock(
            id="doc1",
            score=0.9,
            payload={"content": "Test result", "metadata": {"source": "test"}},
        )
    ]
    mock.delete.return_value = Mock()
    return mock


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock = Mock()
    mock.embeddings.create.return_value = Mock(
        data=[Mock(embedding=np.random.rand(1536).tolist()) for _ in range(5)]
    )
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    mock.pipeline.return_value.__aenter__ = AsyncMock(return_value=mock)
    mock.pipeline.return_value.__aexit__ = AsyncMock(return_value=None)
    mock.execute.return_value = []
    return mock


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "embedding_dimension": 1536,
        "batch_size": 10,
        "top_k": 10,
        "min_score": 0.7,
    }


# Performance test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "stress: mark test as stress test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "integration: mark test as integration test")


# Skip performance tests by default unless explicitly requested
def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle performance tests."""
    if not config.getoption("--run-performance"):
        skip_performance = pytest.mark.skip(
            reason="Performance tests skipped by default"
        )
        for item in items:
            if "performance" in item.keywords:
                item.add_marker(skip_performance)

    if not config.getoption("--run-stress"):
        skip_stress = pytest.mark.skip(reason="Stress tests skipped by default")
        for item in items:
            if "stress" in item.keywords:
                item.add_marker(skip_stress)


def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests",
    )
    parser.addoption(
        "--run-stress", action="store_true", default=False, help="Run stress tests"
    )
    parser.addoption(
        "--run-e2e", action="store_true", default=False, help="Run end-to-end tests"
    )
