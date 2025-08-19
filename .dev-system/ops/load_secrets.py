"""
Load secrets from dev-system config for testing
"""

import os
import sys
from pathlib import Path

def load_dev_secrets():
    """Load secrets from dev-system config file"""
    DEV_SYSTEM_ROOT = Path(__file__).parent.parent
    secrets_file = DEV_SYSTEM_ROOT / "config" / "secrets.env"
    
    if not secrets_file.exists():
        print("❌ No secrets file found")
        return False
    
    # Load secrets into environment
    with open(secrets_file) as f:
        for line in f:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
                print(f"✅ Loaded: {key.strip()}")
    
    return True

if __name__ == "__main__":
    load_dev_secrets()