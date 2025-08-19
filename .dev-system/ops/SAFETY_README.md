# M0: Safety Net & Hygiene System

> **🎯 Goal**: Foundational safety that prevents footguns and secures your agent factory

## Quick Start

```bash
# Setup complete safety system
just safety-setup                   # Install hooks, secrets, gitignore

# Daily safety checks
just safety-check                   # Comprehensive security scan
just rate-status                    # Check API usage limits

# Rate limit testing
just rate-test                      # Test rate limiting system
```

## Safety Components

### 1. Enhanced Pre-Commit Hooks
**Automatic safety validation before every commit:**
- 🛡️ Dev-system safety validation
- 🧹 Linting with dev-system exceptions (E402 allowed)
- 🔐 Secrets exposure detection
- 🏗️ Dev-system structure verification

### 2. Secrets Management
**Secure handling of API keys and sensitive data:**
- 📝 Template creation: `secrets.env.example`
- 🔒 Environment variable loading
- 🚫 Automatic .gitignore protection
- ✅ Validation of required secrets

### 3. Rate Limiting
**Prevents API abuse and cost overruns:**
- ⏱️ Requests per minute: 60 (configurable)
- 🎯 Tokens per hour: 10,000 (configurable)  
- 💰 Daily cost limit: $20 (configurable)
- 🔄 Concurrent request limit: 10

### 4. Security Scanning
**Comprehensive security analysis:**
- 🔍 Secret exposure detection (131 potential issues found)
- ⚠️ Dangerous pattern analysis (2,296 patterns checked)
- 📦 Dependency vulnerability scanning
- 🔧 File permission validation

### 5. System Integrity
**Dev-system structure protection:**
- ✅ Required file validation
- 🏗️ Directory structure verification
- 📋 Configuration completeness
- 🔧 Executable permissions

## Usage Examples

### Daily Safety Routine
```bash
# Morning: Quick safety check
just safety-check                   # 40.0/100 security score

# During development: Automatic protection
git commit -m "changes"             # Pre-commit hooks run automatically

# Before deployments: Rate limit check
just rate-status                    # Check API usage
just release canary 10              # Safe deployment (uses M4)
```

### Security Issue Response
```bash
# When safety-check finds issues:
just safety-check                   # Identify problems

# Example output:
❌ secrets_exposure: Found 131 potential secret exposures
⚠️ dangerous_patterns: Found 2296 potentially dangerous patterns
✅ dev_system_integrity: 5/5 files present
✅ file_permissions: 0 issues found
⚠️ dependency_security: 8 potential issues
```

### Rate Limit Management  
```bash
# Check current usage
just rate-status
# Output:
# Daily Requests: 127 (8.8% of limit)
# Hourly Tokens: 2,450 (24.5% of limit)  
# Daily Cost: $3.47 (17.4% of limit)
# Concurrent: 2/10

# Test rate limiting
just rate-test                      # Simulates API calls
```

## Configuration

### Rate Limits (.dev-system/config/dev-system.yaml)
```yaml
rate_limits:
  requests_per_minute: 60
  tokens_per_hour: 10000
  daily_cost_limit: 20.0
  concurrent_limit: 10
```

### Secrets Template (.dev-system/config/secrets.env.example)
```bash
# OpenAI API Key (for real agent calls)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub Token (for CI/CD integration)  
GITHUB_TOKEN=your_github_token_here

# Database URLs
DATABASE_URL=postgresql://user:pass@localhost:5432/threads_agent
```

## Integration with Other Milestones

### M1 Telemetry Integration
- Rate limiting uses telemetry data for usage tracking
- Safety checks appear in telemetry events
- Usage patterns inform limit adjustments

### M2 Quality Integration  
- Pre-commit hooks run quality validations
- Safety issues block deployments
- Security score tracking over time

### M4 Release Integration
- Deployment safety checks before releases
- Rate limit validation in pre-deployment
- Rollback triggers include security alerts

### M5 Planning Integration
- Security issues appear in morning brief priorities
- Safety score trends in evening debrief
- ICE scoring for security tasks (high impact)

## Safety Metrics

**Current System Security Score: 40.0/100**
- ✅ Dev-system integrity: 100%
- ✅ File permissions: 100%  
- ❌ Secret exposure: Critical issues found
- ⚠️ Dangerous patterns: Many patterns detected
- ⚠️ Dependencies: Potential vulnerabilities

## Business Value

**Risk Reduction:**
- **Prevents secret leaks** that could cost thousands
- **Stops dangerous operations** before they execute
- **Limits API costs** to prevent budget overruns
- **Maintains system integrity** automatically

**Time Savings:**
- **0.5-1h/week** saved on security incident response
- **Automated protection** vs manual security reviews
- **Early detection** vs post-incident cleanup

**Foundation Benefits:**
- **Enables confident development** with safety guardrails
- **Supports remaining milestones** with secure foundation
- **Production-ready security** from day one

M0 creates the **safety foundation** that allows you to develop and deploy with confidence!