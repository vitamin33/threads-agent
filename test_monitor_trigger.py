#!/usr/bin/env python3
"""
New test file to trigger CI monitor auto-fix with PAT push
"""

# Import error
from typing import List
import datetime

def bad_function(items: List[str]) -> int:
    # Type error: should return int but returns str
    result = json.dumps(items)  # json not imported
    return result

# Indentation error
def another_function():
     value = 42
    return value

# Unused imports and variables
import os
unused_var = "test"

# Missing type annotation
def process_data(data):
    return len(data)