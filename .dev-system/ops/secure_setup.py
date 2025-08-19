"""
Secure Setup Helper for Dev-System
Guides secure configuration without exposing secrets
"""

import os
import sys
from pathlib import Path

def configure_openai_key():
    """Securely configure OpenAI key"""
    print("🔑 OpenAI API Key Configuration")
    print("=" * 40)
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Create a new key (if you don't have one)")
    print("3. Copy the key")
    print("4. Run: export OPENAI_API_KEY=your_key_here")
    print("5. Or edit .dev-system/config/secrets.env manually")
    print()
    print("⚠️  NEVER share API keys in chat or commit them to git!")
    
def configure_github_token():
    """Securely configure GitHub token"""
    print("🔑 GitHub Token Configuration")  
    print("=" * 40)
    print("1. Go to: https://github.com/settings/tokens")
    print("2. Generate new token (classic)")
    print("3. Required scopes: repo, workflow, write:packages")
    print("4. Copy the token")
    print("5. Run: export GITHUB_TOKEN=your_token_here")
    print("6. Or edit .dev-system/config/secrets.env manually")
    print()
    print("⚠️  NEVER share tokens in chat or commit them to git!")

def check_environment_setup():
    """Check if secrets are available in environment"""
    print("🔍 Environment Check")
    print("=" * 40)
    
    # Check OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        print(f"✅ OPENAI_API_KEY: Present (starts with: {openai_key[:7]}...)")
    else:
        print("❌ OPENAI_API_KEY: Not found")
        print("   Add with: export OPENAI_API_KEY=your_key_here")
    
    # Check GitHub
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        print(f"✅ GITHUB_TOKEN: Present (starts with: {github_token[:7]}...)")
    else:
        print("❌ GITHUB_TOKEN: Not found")
        print("   Add with: export GITHUB_TOKEN=your_token_here")
    
    # Check mock mode
    mock_mode = os.getenv('OPENAI_MOCK', '0')
    print(f"ℹ️  Mock Mode: {'Enabled' if mock_mode == '1' else 'Disabled'}")
    
    print()
    if openai_key or mock_mode == '1':
        print("✅ Dev-system ready to use!")
    else:
        print("⚠️  Add OPENAI_API_KEY or enable mock mode")

def main():
    """Interactive setup guide"""
    print("🚀 Secure Dev-System Configuration Guide")
    print("=" * 50)
    print()
    
    configure_openai_key()
    print()
    configure_github_token()
    print()
    check_environment_setup()
    
    print()
    print("🛡️  Security Reminders:")
    print("  • Keys exposed in chat should be revoked immediately")
    print("  • Use environment variables for production")
    print("  • Test with mock mode first (OPENAI_MOCK=1)")
    print("  • Monitor usage with: just rate-status")

if __name__ == "__main__":
    main()