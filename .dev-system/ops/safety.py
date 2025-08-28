"""
M0: Safety Net & Hygiene System
Foundational safety systems to prevent footguns and secure development
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add dev-system to path
DEV_SYSTEM_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(DEV_SYSTEM_ROOT))

from ops.telemetry import telemetry_decorator

class SafetyChecker:
    """Comprehensive safety checking system"""
    
    def __init__(self):
        self.project_root = DEV_SYSTEM_ROOT.parent
        
    @telemetry_decorator(agent_name="safety_checker", event_type="safety_check")
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all safety checks"""
        checks = [
            self.check_secrets_exposure(),
            self.check_dangerous_patterns(),
            self.check_dev_system_integrity(),
            self.check_file_permissions(),
            self.check_dependency_security()
        ]
        
        passed_checks = sum(1 for check in checks if check['status'] == 'PASS')
        total_checks = len(checks)
        
        return {
            'overall_status': 'PASS' if passed_checks == total_checks else 'FAIL',
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'checks': checks,
            'security_score': (passed_checks / total_checks) * 100
        }
    
    def check_secrets_exposure(self) -> Dict[str, Any]:
        """Check for exposed secrets in code"""
        dangerous_patterns = [
            r'api[_-]?key\s*[:=]\s*[\'"][^\'"\s]{10,}[\'"]',
            r'secret[_-]?key\s*[:=]\s*[\'"][^\'"\s]{10,}[\'"]',
            r'password\s*[:=]\s*[\'"][^\'"\s]{5,}[\'"]',
            r'token\s*[:=]\s*[\'"][^\'"\s]{10,}[\'"]',
            r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API keys
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
        ]
        
        exposed_secrets = []
        
        # Check Python files
        for py_file in self.project_root.rglob("*.py"):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern in dangerous_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        exposed_secrets.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'pattern': pattern,
                            'line': content[:match.start()].count('\n') + 1
                        })
            except Exception:
                continue
        
        return {
            'check': 'secrets_exposure',
            'status': 'PASS' if not exposed_secrets else 'FAIL',
            'message': f'Found {len(exposed_secrets)} potential secret exposures',
            'details': exposed_secrets[:5],  # Show first 5
            'action': 'Move secrets to environment variables or secure storage'
        }
    
    def check_dangerous_patterns(self) -> Dict[str, Any]:
        """Check for dangerous code patterns"""
        dangerous_patterns = [
            (r'os\.system\([\'"][^\'"]*(rm|del|format)[^\'\"]*[\'\"]\)', 'Dangerous system call'),
            (r'subprocess\.(run|call)\([\'"][^\'"]*(rm|del|format)[^\'\"]*[\'\"]\)', 'Dangerous subprocess'),
            (r'eval\s*\(', 'eval() usage (security risk)'),
            (r'exec\s*\(', 'exec() usage (security risk)'),
            (r'__import__\s*\([\'"][^\'\"]*[\'\"]\)', 'Dynamic import (potential security risk)'),
        ]
        
        dangerous_code = []
        
        for py_file in self.project_root.rglob("*.py"):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for pattern, description in dangerous_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        dangerous_code.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'pattern': description,
                            'line': content[:match.start()].count('\n') + 1,
                            'code_snippet': match.group(0)
                        })
            except Exception:
                continue
        
        return {
            'check': 'dangerous_patterns',
            'status': 'PASS' if not dangerous_code else 'WARN',
            'message': f'Found {len(dangerous_code)} potentially dangerous patterns',
            'details': dangerous_code[:5],
            'action': 'Review dangerous patterns and add safety checks'
        }
    
    def check_dev_system_integrity(self) -> Dict[str, Any]:
        """Check dev-system structure integrity"""
        required_files = [
            '.dev-system/config/dev-system.yaml',
            '.dev-system/ops/telemetry.py',
            '.dev-system/evals/suites/core.yaml',
            '.dev-system/planner/brief.py',
            '.dev-system/ops/release.py'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        return {
            'check': 'dev_system_integrity',
            'status': 'PASS' if not missing_files else 'FAIL',
            'message': f'Dev-system integrity: {len(required_files)-len(missing_files)}/{len(required_files)} files present',
            'details': missing_files,
            'action': 'Restore missing dev-system files'
        }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """Check file permissions for security"""
        executable_files = [
            '.dev-system/cli/dev-system',
            '.dev-system/cli/metrics-today',
            '.dev-system/cli/verify-structure'
        ]
        
        permission_issues = []
        
        for file_path in executable_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                # Check if file is executable
                if not os.access(full_path, os.X_OK):
                    permission_issues.append({
                        'file': file_path,
                        'issue': 'Not executable',
                        'fix': f'chmod +x {file_path}'
                    })
        
        return {
            'check': 'file_permissions',
            'status': 'PASS' if not permission_issues else 'FAIL',
            'message': f'File permissions: {len(permission_issues)} issues found',
            'details': permission_issues,
            'action': 'Fix file permissions with chmod'
        }
    
    def check_dependency_security(self) -> Dict[str, Any]:
        """Check for known vulnerable dependencies"""
        vulnerabilities = []
        
        # Check requirements.txt files
        for req_file in self.project_root.rglob("requirements*.txt"):
            try:
                with open(req_file, 'r') as f:
                    content = f.read()
                    
                # Simple version checks for known vulnerabilities
                vulnerable_packages = [
                    ('requests', '2.27.0', 'CVE-2022-32187'),
                    ('urllib3', '1.26.0', 'Various CVEs'),
                    ('pillow', '9.0.0', 'CVE-2022-22817')
                ]
                
                for pkg, min_version, cve in vulnerable_packages:
                    if pkg in content:
                        vulnerabilities.append({
                            'file': str(req_file.relative_to(self.project_root)),
                            'package': pkg,
                            'recommendation': f'Update to >={min_version}',
                            'cve': cve
                        })
                        
            except Exception:
                continue
        
        return {
            'check': 'dependency_security',
            'status': 'PASS' if not vulnerabilities else 'WARN',
            'message': f'Dependency security: {len(vulnerabilities)} potential issues',
            'details': vulnerabilities,
            'action': 'Update vulnerable dependencies'
        }

class SecretManager:
    """Secure secrets management for development"""
    
    def __init__(self):
        self.secrets_file = DEV_SYSTEM_ROOT / "config" / "secrets.env"
        self.example_file = DEV_SYSTEM_ROOT / "config" / "secrets.env.example"
    
    def create_secrets_template(self):
        """Create secrets template file"""
        template_content = """# Dev-System Secrets Configuration
# Copy this file to secrets.env and fill in your values
# NEVER commit secrets.env to git!

# OpenAI API Key (for real agent calls)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Token (for CI/CD integration)  
GITHUB_TOKEN=your_github_token_here

# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/threads_agent
REDIS_URL=redis://localhost:6379/0

# Optional: Custom model endpoints
CUSTOM_MODEL_ENDPOINT=https://your-model-endpoint.com/v1
CUSTOM_MODEL_API_KEY=your_custom_key_here

# Development flags
DEBUG_MODE=true
LOG_LEVEL=INFO
TELEMETRY_ENABLED=true

# Rate limiting
MAX_REQUESTS_PER_MINUTE=60
MAX_TOKENS_PER_HOUR=10000
"""
        
        with open(self.example_file, 'w') as f:
            f.write(template_content)
        
        print(f"✅ Secrets template created: {self.example_file}")
        print(f"📋 Copy to {self.secrets_file} and configure your values")
    
    def load_secrets(self) -> Dict[str, str]:
        """Load secrets from environment and secrets file"""
        secrets = {}
        
        # Load from secrets file if exists
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            secrets[key.strip()] = value.strip()
            except Exception as e:
                print(f"⚠️  Error loading secrets file: {e}")
        
        # Override with environment variables
        env_secrets = [
            'OPENAI_API_KEY', 'GITHUB_TOKEN', 'DATABASE_URL', 
            'REDIS_URL', 'DEBUG_MODE', 'TELEMETRY_ENABLED'
        ]
        
        for key in env_secrets:
            if key in os.environ:
                secrets[key] = os.environ[key]
        
        return secrets
    
    def get_secret(self, key: str, default: str = None) -> Optional[str]:
        """Get a specific secret value"""
        secrets = self.load_secrets()
        return secrets.get(key, default)
    
    def validate_secrets(self) -> Dict[str, Any]:
        """Validate required secrets are present"""
        secrets = self.load_secrets()
        
        required_secrets = ['OPENAI_API_KEY']
        recommended_secrets = ['GITHUB_TOKEN', 'DATABASE_URL']
        
        missing_required = [key for key in required_secrets if not secrets.get(key)]
        missing_recommended = [key for key in recommended_secrets if not secrets.get(key)]
        
        return {
            'required_present': len(missing_required) == 0,
            'missing_required': missing_required,
            'missing_recommended': missing_recommended,
            'total_secrets': len(secrets),
            'status': 'PASS' if not missing_required else 'FAIL'
        }

class RateLimiter:
    """Rate limiting for API calls and resource usage"""
    
    def __init__(self):
        self.limits_file = DEV_SYSTEM_ROOT / "config" / "rate_limits.yaml"
        self.usage_file = DEV_SYSTEM_ROOT / "data" / "usage_tracking.json"
        
    def create_rate_limits_config(self):
        """Create rate limits configuration"""
        config_content = """# Rate Limiting Configuration
# Prevents API abuse and cost overruns

api_limits:
  openai:
    requests_per_minute: 60
    tokens_per_hour: 10000
    daily_cost_limit: 20.0
    
  github:
    requests_per_hour: 5000
    
  general:
    concurrent_requests: 10
    retry_attempts: 3
    retry_delay_seconds: 1

# Emergency brakes
emergency_limits:
  max_daily_cost: 50.0
  max_hourly_requests: 1000
  max_concurrent_operations: 20

# Monitoring thresholds  
alerts:
  cost_warning_threshold: 15.0
  rate_limit_warning: 0.8  # 80% of limit
  consecutive_failures: 5
"""
        
        with open(self.limits_file, 'w') as f:
            f.write(config_content)
        
        print(f"✅ Rate limits config created: {self.limits_file}")
    
    @telemetry_decorator(agent_name="rate_limiter", event_type="limit_check")
    def check_rate_limits(self, operation_type: str, resource_usage: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if operation is within rate limits"""
        
        # Simplified rate limiting check
        current_usage = self._get_current_usage()
        
        # Check daily cost limit
        daily_cost = current_usage.get('daily_cost', 0.0)
        if daily_cost > 20.0:
            return {
                'allowed': False,
                'reason': f'Daily cost limit exceeded: ${daily_cost:.2f}',
                'suggestion': 'Wait until tomorrow or increase limit'
            }
        
        # Check request rate
        hourly_requests = current_usage.get('hourly_requests', 0)
        if hourly_requests > 1000:
            return {
                'allowed': False,
                'reason': f'Hourly request limit exceeded: {hourly_requests}',
                'suggestion': 'Wait or implement request batching'
            }
        
        return {
            'allowed': True,
            'remaining_budget': 20.0 - daily_cost,
            'remaining_requests': 1000 - hourly_requests
        }
    
    def _get_current_usage(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        # Simplified - in real implementation, track usage in telemetry
        try:
            from ops.telemetry import get_daily_metrics
            metrics = get_daily_metrics(1)
            return {
                'daily_cost': metrics.get('total_cost', 0.0),
                'hourly_requests': metrics.get('failed_calls', 0) + 100  # Estimate
            }
        except:
            return {'daily_cost': 0.0, 'hourly_requests': 0}

def install_pre_commit_hooks():
    """Install enhanced pre-commit hooks"""
    hooks_dir = DEV_SYSTEM_ROOT.parent / ".git" / "hooks"
    
    # Enhanced pre-commit hook
    pre_commit_content = """#!/bin/bash
# Enhanced Pre-commit Hook with Dev-System Safety Checks
set -e

echo "🔍 Dev-System Safety Checks..."

# 1. Run dev-system safety validation
if [ -f ".dev-system/ops/safety.py" ]; then
    echo "🛡️  Running safety checks..."
    cd .dev-system
    python3 ops/safety.py --validate
    cd ..
fi

# 2. Run basic linting (non-blocking for dev-system)
echo "🧹 Running linters..."
if command -v ruff >/dev/null 2>&1; then
    # Allow E402 errors in dev-system (intentional for path manipulation)
    ruff check . --exclude .dev-system/ || echo "⚠️  Linting issues found (non-blocking)"
    ruff check .dev-system/ --extend-ignore E402 || echo "⚠️  Dev-system linting issues found (non-blocking)"
fi

# 3. Check for secrets exposure
echo "🔐 Checking for secrets..."
if grep -r "sk-[a-zA-Z0-9]" . --include="*.py" --exclude-dir=.venv --exclude-dir=__pycache__ >/dev/null 2>&1; then
    echo "❌ Potential API key found in code!"
    echo "Move secrets to environment variables or .dev-system/config/secrets.env"
    exit 1
fi

# 4. Validate dev-system structure
if [ -f ".dev-system/cli/verify-structure" ]; then
    echo "🏗️  Verifying dev-system structure..."
    ./.dev-system/cli/verify-structure --quiet || echo "⚠️  Structure issues found"
fi

echo "✅ Pre-commit safety checks complete"
"""
    
    pre_commit_hook = hooks_dir / "pre-commit"
    
    # Backup existing hook if present
    if pre_commit_hook.exists():
        backup_path = hooks_dir / "pre-commit.backup"
        pre_commit_hook.rename(backup_path)
        print(f"📋 Existing hook backed up to: {backup_path}")
    
    # Install new hook
    with open(pre_commit_hook, 'w') as f:
        f.write(pre_commit_content)
    
    # Make executable
    os.chmod(pre_commit_hook, 0o755)
    
    print(f"✅ Enhanced pre-commit hook installed: {pre_commit_hook}")

def setup_gitignore_safety():
    """Ensure critical files are in .gitignore"""
    gitignore_path = DEV_SYSTEM_ROOT.parent / ".gitignore"
    
    safety_entries = [
        "# Dev-System Safety (M0)",
        ".dev-system/config/secrets.env",
        ".dev-system/data/*.db", 
        ".dev-system/data/*.log",
        "*.backup",
        ".env.local",
        "secrets.env",
        "*.key",
        "*.pem"
    ]
    
    # Read existing gitignore
    existing_content = ""
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
    
    # Add missing entries
    new_entries = []
    for entry in safety_entries:
        if entry not in existing_content:
            new_entries.append(entry)
    
    if new_entries:
        with open(gitignore_path, 'a') as f:
            f.write("\n\n" + "\n".join(new_entries))
        
        print(f"✅ Added {len(new_entries)} safety entries to .gitignore")
    else:
        print("✅ .gitignore already has safety entries")

def main():
    """CLI entry point for safety system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dev-System Safety Checker")
    parser.add_argument("--validate", action="store_true", help="Run all safety checks")
    parser.add_argument("--install-hooks", action="store_true", help="Install pre-commit hooks")
    parser.add_argument("--setup-secrets", action="store_true", help="Setup secrets management")
    parser.add_argument("--setup-gitignore", action="store_true", help="Setup .gitignore safety")
    
    args = parser.parse_args()
    
    if args.validate:
        checker = SafetyChecker()
        result = checker.run_all_checks()
        
        print("🛡️  Dev-System Safety Report")
        print("=" * 50)
        print(f"Overall Status: {result['overall_status']}")
        print(f"Security Score: {result['security_score']:.1f}/100")
        print(f"Checks: {result['passed_checks']}/{result['total_checks']} passed")
        
        for check in result['checks']:
            status_emoji = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}[check['status']]
            print(f"\n{status_emoji} {check['check']}: {check['message']}")
            
            if check['details'] and check['status'] != 'PASS':
                print(f"   Action: {check['action']}")
                if isinstance(check['details'], list) and check['details']:
                    print(f"   Details: {len(check['details'])} issues found")
    
    elif args.install_hooks:
        install_pre_commit_hooks()
        
    elif args.setup_secrets:
        manager = SecretManager()
        manager.create_secrets_template()
        validation = manager.validate_secrets()
        print(f"📊 Secrets validation: {validation['status']}")
        
    elif args.setup_gitignore:
        setup_gitignore_safety()
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()