#!/usr/bin/env python3
"""
This file intentionally has errors to trigger CI failures:
1. Type annotation error
2. Import error  
3. Syntax/formatting error
"""

# Missing import
from typing import List, Dict

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

if __name__ == "__main__":
    # This will fail
    data = '{"test": true}'
    process_data(data)
    print("Done")