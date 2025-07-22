<!-- title & badges -->

# Threads-Agent Stack 🧵🤖

[![CI (dev)](.github/workflows/dev-ci.yml/badge.svg)](../../actions/workflows/dev-ci.yml)
![license](https://img.shields.io/badge/license-MIT-blue)

<!-- add Codecov, FinOps, etc. badges later -->

---

## ✨ What is this?

> **Threads-Agent Stack** – a full-stack, multi-persona AI agent that
> researches trends ➜ writes & posts Threads content ➜ measures ROI – all on a
> production-grade Kubernetes architecture.
> **Goal**: prove 6 %+ ER and $0.01 cost/follow, then scale to \$20 k MRR.
> 
> **NEW**: Real Threads API integration for actual posting and engagement tracking!

_Micro-services:_ Orchestrator · Persona-runtime (LangGraph + LoRA) · Bandit
online A/B · Trend & Pain Flywheel · FinOps board · SRE/Chaos add-ons.

---

## 🖼 Architecture (dev vs prod)

![infra diagram](docs/infra.svg)

- **Local dev** → `k3d` (K3s in Docker), Helm mono-chart, OTEL → Jaeger.
- **Stage / Prod** → AWS EKS spot, Aurora Sls, Qdrant + replica, autoscale,
  Vault + external-secrets.

---

## ⚡ Quick-start (local)

### 🎯 NEW: 80/20 Productivity Mode
```bash
# The ONLY commands you need daily:
just work-day        # Start everything (morning)
just create-viral    # AI creates viral content
just make-money      # Run business on autopilot

# See: QUICK_REFERENCE.md for all mega commands
```

### Traditional Setup
```bash
# 0 · prereqs: Docker >= 24, k3d >= 5.6, Helm >= 3.14, Python 3.11
git clone git@github.com:threads-agent-stack/threads-agent.git
cd threads-agent
just bootstrap        # → k3d cluster dev
just deploy-dev       # → helm install threads
just test             # → pytest (unit + e2e)
open http://localhost:16686   # Jaeger UI
```

### 🔌 Real Threads API Integration (NEW!)
```bash
# Enable real posting to Threads (replaces fake-threads)
# 1. Get credentials from Meta Developer Dashboard
# 2. Configure in chart/values-dev.yaml
# 3. See full setup guide:
cat docs/threads-api-setup.md

# Quick test:
just threads-health          # Check API connection
just threads-test-post       # Post to real Threads
just threads-refresh-metrics # Get engagement data
```

---

## 💻 Repo layout

| Path / File           | Purpose                                                       |
| --------------------- | ------------------------------------------------------------- |
| `services/`           | All micro-services (orchestrator, persona-runtime, bandit, …) |
| `chart/`              | Helm mono-chart + `values-*.yaml`                             |
| `infra/terraform/`    | VPC / EKS / RDS IaC (staging & prod)                          |
| `infra/helmfile.yaml` | Multi-env release orchestration                               |
| `docs/`               | Diagrams, cost sheet, white-papers, chaos playbook            |
| `scripts/`            | `dev-up.sh`, chaos runner, backlog→Linear importer            |
| `tests/`              | `unit/`, `e2e/`, `security/` suites                           |
| `.github/workflows/`  | CI (dev), CD (prod), security-scan, chaos-ci                  |

---

## 🔑 Code ownership & PR rules

_See [.github/CODEOWNERS](.github/CODEOWNERS) for full mapping._

- `main` is **protected** – every PR must:
  1. pass **CI (dev)** checks;
  2. receive at least one ✅ from the relevant code owners.

---

## 🗺 Roadmap (epics)

| Epic                                            | Status         | Timeline      |
| ----------------------------------------------- | -------------- | ------------- |
| **E1 – Core MVP (templates)**                   | ✅ completed   | Completed     |
| **E2 – Core MVP (IMPL)**                        | ✅ completed   | Completed     |
| **E3 – SRE v1: Advanced Monitoring & Alerting** | ✅ completed   | Completed     |
| **E3.5 – Revenue Foundation + Viral Core**      | 🟡 in progress | Jul 29 - Aug 2|
| **E4 – Advanced Multi-Variant Testing**         | ⬜ planned     | Aug 2 - 5     |
| **E5 – DM-to-Purchase Pipeline**                | ⬜ planned     | Aug 5 - 7     |
| **E6 – Viral Observability & FinOps**           | ⬜ planned     | Aug 7 - 12    |
| **E7 – Viral Learning Flywheel**                | ⬜ planned     | Aug 12 - 18   |
| **E8 – Premium Intelligence Products**          | ⬜ planned     | Aug 18 - 20   |
| **E9 – Intelligent Engagement Engine**          | ⬜ planned     | Aug 20 - 25   |
| **E10 – Engagement Guarantee System**           | ⬜ planned     | Aug 25 - 27   |
| **E11 – Scale Validation**                      | ⬜ planned     | Aug 27 - 30   |
| **E12 – Portfolio Polish**                      | ⬜ planned     | Aug 30 - Sep 6|

_(Live backlog & task breakdown lives in Linear → link in repo description.)_

---

## 🤝 Contributing

1. Fork → feature branch `feat/<epic>-<slug>`
2. `just bootstrap && just test` – ensure green locally
3. Open PR → automatic reviewer assignment via CODEOWNERS
4. At least one ✔ review + passing **CI (dev)** ➜ merge

### Port-forward stubs

```bash
# Postgres → localhost:5432
kubectl port-forward svc/postgres 5432:5432

# Fake Threads → localhost:9009
kubectl port-forward svc/fake-threads 9009:9009
curl localhost:9009/ping  # → {"pong":true}
```

## 6. Verify

```bash
just dev-up          # your k3d helper
helm upgrade --install threads ./chart -f chart/values-dev.yaml --wait
kubectl get pods     # postgres & fake-threads Ready
curl fake-threads:9009/ping         # inside cluster
```

---

## 🤖 AI-Assisted Development

This project uses Claude Code with MCP servers for intelligent development assistance.

**📖 Complete Guide**: See [CLAUDE_CODE_GUIDE.md](./CLAUDE_CODE_GUIDE.md) for comprehensive workflows, commands, and best practices.

**🚀 Quick Start**:

```bash
session    # Start development session
next       # Get immediate next action
sprint     # Current sprint status
```

## 📝 License

MIT © 2025 Threads-Agent Stack Contributors
