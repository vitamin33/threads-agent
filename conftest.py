"""Global pytest configuration to disable langsmith."""

import os
import sys
import inspect

# Disable langsmith/langchain tracing before any imports
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"
os.environ["LANGCHAIN_CALLBACKS_MANAGER"] = "false"
os.environ["LANGSMITH_API_KEY"] = ""
os.environ["LANGCHAIN_API_KEY"] = ""

# Python 3.12+ ForwardRef compatibility patch for langsmith
if sys.version_info >= (3, 12):
    try:
        from typing import ForwardRef

        # Check if _evaluate method exists and needs patching
        if hasattr(ForwardRef, "_evaluate"):
            original_evaluate = ForwardRef._evaluate
            sig = inspect.signature(original_evaluate)

            # Only patch if 'recursive_guard' is missing from signature
            if "recursive_guard" not in sig.parameters:

                def patched_evaluate(
                    self,
                    globalns=None,
                    localns=None,
                    frozenset=frozenset,
                    recursive_guard=None,
                ):
                    # Call original method without recursive_guard
                    return original_evaluate(self, globalns, localns, frozenset)

                ForwardRef._evaluate = patched_evaluate
    except Exception:
        # Silently ignore if patching fails
        pass
