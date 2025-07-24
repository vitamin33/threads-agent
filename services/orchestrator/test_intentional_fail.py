"""
This file has intentional errors to trigger CI failures for auto-fix demo.
"""

from typing import List, Dict

# Error 1: Missing import
def process_json_data(data: str) -> Dict:
    # json module not imported
    return json.loads(data)

# Error 2: Type mismatch
def calculate_sum(numbers: List[int]) -> None:
    # Should return int, not None
    total = sum(numbers)
    return total

# Error 3: Undefined variable
def get_config():
    # CONFIG not defined
    return CONFIG.get('setting')

# Error 4: Wrong indentation
def format_message(msg: str) -> str:
     # Bad indentation
  result = f"Message: {msg}"
     return result

# Error 5: Missing type annotation
def multiply(a, b):
    return a * b