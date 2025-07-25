"""Test-specific pytest configuration."""

import os
import warnings

# Disable langsmith/langchain tracing before any imports
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_CALLBACKS_MANAGER"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""

# Suppress pydantic v1/v2 compatibility warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
