# 🔒 Secure Dev-System Setup Guide

## Step-by-Step Instructions

### **Step 1: Configure OpenAI API Key**

```bash
# Edit the secrets file
nano .dev-system/config/secrets.env

# Update this line:
OPENAI_API_KEY=test_key_validation

# With your actual key:
OPENAI_API_KEY=sk-proj-your_actual_key_here
```

**Where to get OpenAI key:**
1. Go to: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Name it: "dev-system-agent-factory"
4. Copy the key (starts with `sk-proj-...`)
5. Paste it in the secrets file

### **Step 2: Configure GitHub Token**

```bash
# Edit the secrets file
nano .dev-system/config/secrets.env

# Uncomment and update this line:
# GITHUB_TOKEN=ghp_your_token_here

# With your actual token:
GITHUB_TOKEN=ghp_your_actual_token_here
```

**Where to get GitHub token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: "dev-system-automation"
4. Select scopes: `repo`, `workflow`, `write:packages`
5. Generate and copy the token
6. Paste it in the secrets file

### **Step 3: Verify Configuration**

```bash
# Test secrets are loaded correctly
cd .dev-system && python3 ops/secure_setup.py

# Should show:
# ✅ OPENAI_API_KEY: Present (starts with: sk-proj...)
# ✅ GITHUB_TOKEN: Present (starts with: ghp_...)
```

### **Step 4: Test Real System**

```bash
# Test with real OpenAI calls (will cost ~$0.20)
just eval-run core                  # Real quality evaluation

# Test rate limiting with real usage
just rate-status                    # Check current usage

# Test release with real validation
just release canary 10              # Should pass if quality is good
```

### **Step 5: Monitor Usage**

```bash
# Daily monitoring
just metrics-today                  # Check costs and performance
just rate-status                    # Check API usage limits
just safety-check                   # Regular security scan
```

## **🔧 Current File Status**

Your secrets file is now configured for **real usage** (mock disabled):

```bash
# Current config:
OPENAI_MOCK=0                       # ✅ Real mode enabled
DAILY_COST_LIMIT=5.0               # ✅ Conservative $5/day limit
MAX_TOKENS_PER_HOUR=5000           # ✅ Conservative token limit
```

## **🎯 Final Configuration File**

After you add your keys, your `.dev-system/config/secrets.env` should look like:

```bash
# M2 Quality Gates - OpenAI for real evaluation testing
OPENAI_API_KEY=sk-proj-your_actual_key_here
OPENAI_MOCK=0

# GitHub integration - For automated workflows and CI
GITHUB_TOKEN=ghp_your_actual_token_here

# M0 Rate Limiting - Conservative development limits
DAILY_COST_LIMIT=5.0
MAX_REQUESTS_PER_MINUTE=30
MAX_TOKENS_PER_HOUR=5000

# Feature flags
TELEMETRY_ENABLED=true
QUALITY_GATES_ENABLED=true
SAFETY_CHECKS_ENABLED=true
AUTO_ROLLBACK_ENABLED=true
DEBUG_MODE=true
LOG_LEVEL=INFO
```

## **✅ Ready to Use**

Once configured, your **top 1% agent factory** will be fully operational with:
- Real AI quality evaluations
- Automated GitHub integration
- Cost monitoring and protection
- Complete safety net active

**Just add your keys securely to the file - don't share them in chat! 🔑**