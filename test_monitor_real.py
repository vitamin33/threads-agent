#!/usr/bin/env python3
"""
Real test file to trigger CI monitor auto-fix
"""

# Import error - json not imported
from typing import List

def broken_function(data: str) -> int:
    # This will fail - json not imported
    result = json.loads(data)
    return len(result)

# Indentation error
def another_broken_function():
     value = 42  # Bad indentation
    return value

# Type error
def type_error_function(items: List[str]) -> str:
    # Returns int instead of str
    return len(items)

# Missing type annotation
def no_types(data):
    return data

if __name__ == "__main__":
    print("This file will trigger CI failures")