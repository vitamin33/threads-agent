"""Test configuration for vLLM service."""

import os
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_vllm_available():
    """Mock vLLM availability for testing."""
    with patch("services.vllm_service.model_manager.VLLM_AVAILABLE", True):
        yield


@pytest.fixture
def mock_vllm_unavailable():
    """Mock vLLM unavailability for testing fallback mode."""
    with patch("services.vllm_service.model_manager.VLLM_AVAILABLE", False):
        yield


@pytest.fixture
def mock_apple_silicon():
    """Mock Apple Silicon detection."""
    # Mock the entire torch module for testing
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.backends.mps.is_available.return_value = True

    with patch.dict("sys.modules", {"torch": mock_torch}):
        yield


@pytest.fixture
def mock_no_gpu():
    """Mock no GPU available."""
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.backends.mps.is_available.return_value = False

    with patch.dict("sys.modules", {"torch": mock_torch}):
        yield


@pytest.fixture
def test_client():
    """Create test client for vLLM service."""
    # Set test environment variables
    os.environ["VLLM_MODEL"] = "meta-llama/Llama-3.1-8B-Instruct"
    os.environ["FORCE_CPU"] = "true"  # For testing without GPU requirements

    # Mock torch to prevent import errors
    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = False
    mock_torch.backends.mps.is_available.return_value = False

    with patch.dict("sys.modules", {"torch": mock_torch}):
        from services.vllm_service.main import app

        return TestClient(app)


@pytest.fixture
def sample_chat_request():
    """Sample chat completion request."""
    return {
        "model": "llama-3-8b",
        "messages": [
            {
                "role": "user",
                "content": "Write a viral social media hook about productivity",
            }
        ],
        "max_tokens": 256,
        "temperature": 0.7,
    }
