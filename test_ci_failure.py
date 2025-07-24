#!/usr/bin/env python3
"""
This file intentionally has errors to trigger CI failures:
1. Type annotation error
2. Import error  
3. Syntax/formatting error
4. Linting issues
"""

# Missing import
from typing import List, Dict
import os

def process_data(data: str) -> None:
    # Type error: returning int instead of None
    result = json.loads(data)  # json not imported!
    return len(result)

def format_output(items: List[str]) -> str:
    # Formatting error - bad indentation
     output = ""
    for item in items:
        output += f"{item}\n"
    return output

# Missing type annotation
def calculate_total(numbers):
    return sum(numbers)

# Unused variable (linting issue)
def unused_function():
    unused_var = 42
    another_unused = "test"
    return None

# Line too long (formatting issue)
def long_line_function():
    really_long_string = "This is a really long string that exceeds the maximum line length limit and should be wrapped by black formatter to comply with PEP8 standards"
    return really_long_string

if __name__ == "__main__":
    # This will fail
    data = '{"test": true}'
    process_data(data)
    print("Done")