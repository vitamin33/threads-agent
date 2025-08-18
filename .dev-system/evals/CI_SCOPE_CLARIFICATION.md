# M2 CI Scope Clarification

## **Two Separate CI Systems (By Design)**

### **Existing Threads-Agent CI** (.github/workflows/main-ci.yml)
**Scope**: Application functionality and deployment
- ✅ Service unit tests (pytest)
- ✅ Integration tests (e2e)
- ✅ Linting and type checking  
- ✅ Docker builds and K8s deployment
- ✅ Business logic validation

**Purpose**: Ensure threads-agent services work correctly

### **New Dev-System CI** (.github/workflows/m2-quality-gates.yml)  
**Scope**: Agent behavior and development workflow quality
- 🆕 **Agent behavior validation** (prompt → output quality)
- 🆕 **Development workflow gates** (cost, latency, success rate)
- 🆕 **Regression prevention** for AI agent performance
- 🆕 **Quality score enforcement** (engagement prediction accuracy)

**Purpose**: Ensure AI agent development system maintains quality

## **Key Differences**

| Aspect | Threads-Agent CI | Dev-System CI |
|--------|------------------|---------------|
| **Triggers** | All code changes | `.dev-system/**` changes only |
| **Tests** | Unit/integration tests | Golden set evaluations |
| **Validates** | Code correctness | Agent behavior quality |
| **Blocks** | Broken functionality | Poor AI performance |
| **Runtime** | 5-15 minutes | 2-5 minutes |
| **Dependencies** | Full service stack | Minimal (yaml only) |

## **M2 Specific Scope**

**What M2 Quality Gates Check:**
1. **Agent Response Quality** - Does persona_runtime generate good content?
2. **Performance SLAs** - Are responses fast enough (<5s)?  
3. **Cost Efficiency** - Is token usage reasonable (<$10/run)?
4. **Error Handling** - Do agents handle edge cases gracefully?
5. **Behavioral Consistency** - Do agents maintain persona characteristics?

**What M2 Does NOT Check:**
- ❌ Service deployment (existing CI handles this)
- ❌ Database migrations (existing CI handles this)  
- ❌ Docker builds (existing CI handles this)
- ❌ Unit test coverage (existing CI handles this)
- ❌ API endpoint functionality (existing CI handles this)

## **Integration Strategy**

**Complementary Approach:**
- **main-ci.yml**: Ensures services work
- **m2-quality-gates.yml**: Ensures agents perform well

**Trigger Logic:**
```yaml
# M2 only runs when these change:
paths:
  - '.dev-system/**'       # Dev-system files
  - 'services/*/main.py'   # Core agent endpoints  
  - 'services/*/runtime.py' # Agent logic files
```

**No Overlap:**
- M2 uses mock implementations (no real OpenAI calls in CI)
- M2 focuses on agent behavior patterns, not infrastructure
- M2 complements rather than replaces existing quality checks

## **Business Value**

**M2 Prevents These Regressions:**
- 📉 Agent generates lower quality content after prompt changes
- 💰 Token costs spike due to inefficient prompt engineering
- 🐌 Response latency increases above user tolerance
- 🎯 Engagement prediction accuracy degrades
- 💔 Error handling breaks for edge cases

**Existing CI Prevents These:**
- 🚫 Services fail to start or deploy
- 🔧 Database schema issues
- 🐛 API endpoint errors
- 📦 Dependency conflicts

## **Implementation Notes**

**Mock Mode for CI:**
- M2 uses simulated responses in CI (no OpenAI costs)
- Real evaluation runs locally for development
- Focus on behavioral patterns, not exact outputs

**Path-Based Triggering:**
- Only triggers when dev-system or core agent files change
- Prevents unnecessary runs for infrastructure changes
- Keeps CI time efficient

This approach gives you **agent behavior quality assurance** without disrupting your existing robust service CI pipeline.