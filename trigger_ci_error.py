#!/usr/bin/env python3
"""
File with guaranteed CI errors
"""

# This will cause multiple CI failures
import non_existent_module  # Import error

def broken_syntax():
    # Syntax error - missing colon
    if True
        return "broken"

# Indentation error
def bad_indent():
     x = 1
    return x

# This import is used in tests
from services.orchestrator.db.models import Post