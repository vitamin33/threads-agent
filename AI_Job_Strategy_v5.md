# AIjobstrategy.md v5 (Agent Root)

Target role: Remote Senior MLOps + Generative AI Platform Engineer
Comp target: base 180-220k USD or total comp 200k+
Side target: 2-3k MRR from Threads Agent and Achievement Collector

This file is the root instruction for a local 4-agent instances of Claude Code agent. Each agent has a clear scope, owns a swimlane, and ships measurable outputs every week. Each works in separate local git repository.

====================================================================

# 1. Org model: 4 virtual developers

## Agent A - Architect and Planner (main: Vitalii Serbyn)

Scope

- Turn business goals into epics, milestones, and acceptance criteria
- Own system design, trade-offs, security reviews, and risk register
- Maintain OKRs, SLOs, and the weekly plan

Deliverables

- Design docs with C4 and sequence diagrams
- Backlog grooming and sprint plans
- Decision log (ADRs)

Definition of Done

- A design doc exists for each epic with clear trade-offs
- Risks identified with mitigations and owners
- Every ticket has acceptance criteria and test hooks

---

## Agent B - Infra and MLOps (Jordan Kim - jordan-kim)

Scope

- Kubernetes, CI/CD, IaC, observability, build and release
- MLflow or Weights and Biases integration, model registry, feature store hooks

Deliverables

- Helm charts, Terraform modules, GitHub Actions
- Grafana dashboards, alerts, runbooks
- Cost tracking per endpoint and per job

Definition of Done

- Pipelines reproducible from a fresh clone
- Dashboards show p50, p95, error rate, and token cost
- SLO gates enforced in CI

---

## Agent C - Gen AI and Product Features (Riley Morgan - riley-morgan)

Scope

- RAG, prompts, fine-tuning, evaluation
- Threads Agent features, content experiments, guardrails

Deliverables

- Retriever and cache modules, evaluation harness
- Prompt-injection tests and blocked term handling
- A/B experiment framework and reporting

Definition of Done

- Evaluation suite passes with target scores
- Guardrails in CI are green
- Feature behind a toggle with rollback path

---

## Agent D - QA, Evals, Cost and Docs (Sam Chen - sam-chen)

Scope

- End-to-end tests, load tests, failure drills, data quality checks
- Cost benchmarks, carbon notes, release notes and docs

Deliverables

- Locust or k6 load scripts, chaos scripts
- Cost benchmark tables and a what-changed report
- User docs, PR templates, changelogs

Definition of Done

- Baselines recorded and compared on every PR
- Release notes capture risks and mitigations
- Docs updated in the same PR as code

====================================================================

# 2. Operating rhythm

Daily

- 10:00. Agent A posts the day plan and collects blockers
- 19:00. All agents post progress, metrics, and next steps

Weekly

- Monday. Set goals and success metrics for the week
- Wednesday. Mid-week review and adjustments
- Friday. Ship demo video plus metrics, update scoreboard

Monthly

- Review OKRs, reset gates, select a talk or post topic

====================================================================

# 3. North-star metrics and gates

Hiring pipeline

- 4 tailored applications per week
- 2 screens per week after week 3
- 2 finals per month after month 2
- Offer target in 12 weeks or less

Product gates

- Threads Agent p95 under 400 ms at target load, error rate under 0.5 percent
- Achievement Collector ImpactScore R^2 at 0.50 or higher on 30-day windows
- Cost per 1k tokens reduced 30 to 50 percent without latency regressions
- Grafana shows uptime, latency, errors, token cost per endpoint

Social proof

- 2 Loom videos published and linked on the site
- 2 technical posts with 10k or more combined views

Gate policy

- If any gate is missed for 2 weeks, pause new features and fix that gate first

====================================================================

# 4. CI, evals, and SLO gating

Pipelines

- lint -> unit -> integration -> eval -> load-smoke -> security -> deploy-staging

SLO gates

- Block merge if p95 regression is greater than 10 percent vs baseline
- Block merge if error rate exceeds 0.5 percent under smoke load
- Block merge if token cost per request increases more than 15 percent without a documented reason
- Block merge if guardrail tests fail (prompt-injection, PII)

Evaluation suite

- RAG: answer accuracy, context precision and recall, hallucination rate
- Prompt safety: jailbreak set, cross-model adversarial prompts
- Cost: requests per dollar, tokens per request, cache hit rate
- Reliability: retry success percent, circuit-breaker trips, queue depth

Release checklist

- Updated dashboards screenshot in PR
- ADR for any major trade-off
- Rollback plan documented and tested

====================================================================

# 5. Monorepo structure

```
/infra
  /helm
  /terraform
  /github-actions
/achievement_collector
  /api
  /workers
  /eval
  /dashboards
/threads_agent
  /publisher
  /guardrails
  /experiments
  /eval
/common
  /observability
  /auth
  /clients
/docs
  /design
  /runbooks
  /adr
/tests
  /e2e
  /load
```

Branching

- main is protected. Use feat/_, fix/_, ops/\* branches. Conventional commits.

PR template

- Problem, Approach, Metrics before vs after, Risks, Rollback, Screenshots

====================================================================

# 6. Project deliverables and acceptance criteria

## A. Achievement Collector 1.0

- 50 plus PR metrics extracted in CI
- ImpactScore stored per PR with weekly calibration
- Dashboard: R^2 trend, reliability deltas, cost deltas
- Loom: 2 minute demo from PR merge to impact report

ImpactScore v1

```
ImpactScore = 0.25*ReliabilityΔ + 0.20*CostΔ + 0.20*ProductΔ +
              0.15*QualityΔ + 0.10*DeliveryΔ + 0.10*Complexity
```

Data per PR

- delivery: cycle_time, review_depth, revert, hotfix_count
- reliability: error_rate_delta, p95_delta, slo_burn_minutes
- cost: cloud_bill_delta, token_cost_delta, gpu_minutes_delta
- product: conv_rate_delta, support_tickets_delta
- quality: reopen_rate, test_coverage_delta, lint_score_delta
- complexity: {migration|auth|schema|normal}

## B. Threads Agent 1.0

- Idempotent posting, retries with backoff, circuit breaker
- Guardrails in CI, blocked terms, safe rewrite
- 3 variant A/B per post with rotation and metrics
- Dashboard: queue depth, p50, p95, error rate, token cost per post
- Loom: 2 minute guardrails and posting flow

ROI formula

```
dollars_per_post = (visits * conversion_rate * AOV * margin) - (token_cost + infra_cost)
```

====================================================================

# 7. Backlog v1 - first two sprints

Sprint 1 (infra and guardrails)

- Helm charts for both services with HPA
- GitHub Actions: full pipeline and SLO gates
- Prompt-injection test set and blocked term CI job
- Baseline load-smoke with Locust or k6
- Dashboard v1: latency, errors, token cost

Sprint 2 (impact and experiments)

- ImpactScore pipeline with calibration job
- Cost cache for LLM calls, report table
- A/B experiment framework in Threads Agent
- Loom 1 and blog 1 shipped
- Apply to 4 Tier A roles with demo links

====================================================================

# 8. Role prompts for the 4 local agents

Agent A system prompt

```
You are Architect and Planner. Convert goals into epics with clear acceptance criteria, risks, and ADRs. Keep scope realistic. Prefer simple designs. Output: design doc outline, ticket list with sizes, and a weekly plan.
```

Agent B system prompt

```
You are Infra and MLOps. Own K8s, CI/CD, IaC, and observability. Deliver reproducible pipelines, dashboards, and SLO gates. Output: Helm and Terraform diffs, GitHub Actions YAML, Grafana panels, and runbooks.
```

Agent C system prompt

```
You are Gen AI and Features. Build RAG, prompts, and guardrails. Ship toggled features with evaluations and rollback. Output: retriever and cache code, eval results, prompt tests, and feature flags.
```

Agent D system prompt

```
You are QA, Evals, Cost, and Docs. Write load tests, chaos tests, and end-to-end tests. Track costs and produce release notes. Output: test scripts, benchmark tables, and docs changes.
```

Task intake template (for any agent)

```
Goal:
Context:
Success criteria:
Deliverables:
Non-goals:
Risks and mitigations:
Test hooks and metrics:
Timebox: <S|M|L>
```

====================================================================

# 9. Outreach and content

- Publish 1 short technical post per week. Tag any vendor used.
- Two Loom scripts live in docs/design/loom_scripts.md.
- Keep a sheet: company, role, contact, last touch, next step, status.

DM template

```
Hi <name>, I wired <tool> on K8s with guardrails and cut token cost by 41 percent while improving p95 by 32 percent. Here is a 2 minute Loom: <link>. If relevant, happy to share details.
```

====================================================================

# 10. Security and secrets

- No plain secrets in repos. Use Kubernetes Secrets or Vault.
- PII: mask in logs, disable export by default.
- Third-party API keys: rotate monthly. Track in a runbook.

====================================================================

# 11. Review rubric used by the team

Per PR scoring

- Clarity 0 to 2
- Correctness 0 to 2
- Tests and metrics 0 to 2
- Reliability and rollback 0 to 2
- Docs updated 0 to 2

Block merge if score is under 7 or any SLO gate fails.

====================================================================

# 12. Interview prep

- Two mini drills daily: one technical, one behavioral
- Weekly full mock: 20 min design, 10 min scenario, 10 min behavioral, 5 min feedback
- Keep a living doc of STAR stories and cost wins

====================================================================

# 13. What to stop and what to double down on

Stop

- Hand polishing boilerplate
- Shipping features without metrics

Double down

- Architecture, guardrails, cost and reliability numbers
- Short demos with real metrics and clear trade-offs
