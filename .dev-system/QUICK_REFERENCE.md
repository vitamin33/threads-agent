# Agent Factory Quick Reference

## 🌅 **Morning (5 min)**
```bash
just brief                          # AI priorities
just metrics-today                  # System health
just eval-latest                    # Quality check
```

## 🔧 **Development**
```bash
# Before changes
just agent-impact a1                # Check dependencies

# During development  
just eval-run <service>             # Test changes
just safety-check                   # Security

# Prompt work
just prompt-test agent prompt       # Validate prompts
```

## 🚀 **Deployment**
```bash
# Check sequence
just agent-deploy-sequence          # A1→A2+A3→A4

# Deploy safely
just release canary 10              # Safe deployment
just agent-status                   # Verify health
```

## 🌙 **Evening (3 min)**
```bash
just debrief                        # Productivity analysis
just quality-weekly                 # System trends (Fridays)
```

## 🤖 **Multi-Agent**
```bash
just agent-status                   # All agents dashboard
just eval-all                       # Test all agents
just agent-impact a1                # Cross-agent analysis
```

## 📚 **Knowledge & Prompts**
```bash
just knowledge-search "query"       # Find knowledge
just prompt-test agent prompt       # Test prompts
just tool-test openai_chat          # Validate tools
```

## 🛡️ **Security & Quality**
```bash
just safety-check                   # Security scan
just rate-status                    # Usage monitoring
just quality-weekly                 # Quality trends
```

**Total: 13.5-31h/week savings (60-95% efficiency gain)** 🎯