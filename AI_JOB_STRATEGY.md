# AI_JOB_STRATEGY_v11 — One-file plan to land a high-paid remote AI role (US/EU) from Kyiv

**This version integrates your CV (Flutter/Android/full‑stack background) and maps it to AI Platform/MLOps roles.**

## 1) Snapshot

- **You:** Lead/Senior engineer (12+ yrs) with production mobile/web, CI/CD, AWS/GCP, and leadership.
  - Built & led teams; shipped apps with tens of millions of users; heavy CI/CD ownership.
  - Recent AI projects: **Threads‑Agent** (GenAI content platform) and **ROI‑Agent** (multimodal media‑buyer).
- **Constraints:** Remote only from Kyiv; payments via **UK LTD** (company‑only accounts)(not-fully configured yet).
- **Primary roles:** **AI Platform / LLM Infra Engineer** · **Senior MLOps Engineer** · **GenAI Product Engineer (adtech/content)**
- **Target comp:** US remote TC $160–220k (contract $70–120/h). EU/UK remote €80–120k / £80–110k.

---

## 2) 30‑sec pitch (updated for CV)

> “I build **reliable LLM services** the way I shipped high‑traffic mobile apps: tight CI/CD, clear SLOs, and fast rollbacks. I’ve led teams, owned release trains, and now run **LLM pipelines** with observability and cost controls (vLLM + MLflow).”

**Transferable strengths from your CV → AI**

- **Release discipline & CI/CD** → SLO‑gated CI for LLM services, canary + rollback.
- **Large‑scale UX & perf** → p95 latency focus, caching, cold‑start minimization.
- **AWS & GCP exposure** → ECS/EKS minimal deploy, S3/KMS/Secrets, budgets/alarms.
- **Leadership** → incident runbooks, on‑call rituals, mentoring, roadmap execution.
- **Product sense** → pick the metrics that matter (cost/1k tokens, engagement lift).

---

## 3) Market & timeline reality (unchanged)

AI platform/MLOps hiring remains strong vs. broader tech. Remote‑only is viable but fewer postings than hybrid. Expect **3–6 months** to land a top remote role; **8–12 weeks** is possible with volume + proofs. Keep a **contract‑to‑hire** track in parallel.

---

## 4) Portfolio inventory (keep “lite” first)

- **Threads‑Agent‑lite**: API + persona runtime + optimizer + metrics emitter.
- **ROI‑Agent‑lite**: MediaBuyer core + AB engine + policy guardrails + metrics.
  Lead with lite repos (Docker Compose + fake data + clear README). Keep full monorepo for depth.

---

## 5) Gap plan (6–8 weeks) — same priorities

1. **MLflow** tracking + **registry** on both projects; 2 promoted versions; rollback demo.
2. **SLO‑gated CI** (p95, error rate, token‑cost Δ) + **drift** signals/alerts.
3. **vLLM** path and **cost/latency** table under load (requests‑per‑dollar).
4. **Minimal AWS** slice: ECS/EKS, S3, IAM; 2‑min rollback Loom.
5. **A/B** stats (sequential/Bayesian) with one real iteration.
6. **Policy & data hygiene** (Meta Ads): rate limits, policy checks, audit logs, PII masking.

_Nice‑to‑have:_ LoRA fine‑tune; hybrid retrieval cache with measured hit‑rate; chaos drill.

**Artifacts to capture:** 2 Looms, 2 posts, Grafana shots, MLflow registry shots, one‑pager cost/latency, one‑click demo repo.

---

## 6) CV → AI translation (what to emphasize)

**From CV:** 11+ yrs Android/Flutter/Web, CI/CD ownership, AWS (Lambda/Cognito/AppSync/DynamoDB), GCP/K8s, team leadership, 50M+ downloads, QA/process upgrades.
**Tell it like this on the AI resume:**

- **“Production SRE mindset for LLMs.”** Tie your release rigor to SLOs, alerts, rollback.
- **“Cloud‑ready.”** Call out IAM least‑privilege, secrets, budgets; ECS/EKS basics.
- **“Scale & perf.”** Mention p95 goals you hit in mobile and map that discipline to LLM latency & cold starts.
- **“Ownership.”** Led teams, drove CI/CD; now **own model lifecycle** (MLflow), **cost controls** (vLLM), **drift**, **A/B**.
- **“Adtech & content.”** ROI‑Agent and Threads‑Agent match marketing SaaS and content tooling roles.

_Add these keywords for ATS:_ MLflow, model registry, vLLM, RAG, hybrid retrieval, Grafana/Prometheus, K8s/ECS/EKS, CloudWatch, IAM/KMS/Secrets Manager, EventBridge/SQS, A/B sequential tests, drift detection, rollback, canary, SLO p95/error rate, cost per 1k tokens.

---

## 7) Proof Pack v2 (send in every app)

- **Loom #1:** MLflow lifecycle (train→eval→promote) + one‑click rollback.
- **Loom #2:** SLO gate catches perf regression; show Grafana alert → mitigation → steady state.
- **One‑pager:** vLLM vs hosted API p50/p95 + **$ / 1k tokens** + “requests per dollar” chart.
- **Screens:** ImpactScore R² chart, A/B dashboard, drift alert sample.
- **Demo repo:** lite version + Docker Compose + runbook.

---

## 8) Target role matrix (JD keyword → your artifact)

- MLflow/registry → **Registry** with 2 versions, rollback Loom.
- Observability/SRE → **Grafana board** + alert and runbook.
- MLOps/pipelines → **CI** trains/evals, pushes to registry, **gates releases**.
- LLM infra/RAG → multi‑model routing, hybrid retrieval, **semantic cache hit‑rates**.
- Cost optimization → **vLLM vs API** table + requests‑per‑dollar.
- A/B testing → sequential stop or promotion proof.
- Cloud experience → **minimal AWS deploy** + rollback video.
- Security/compliance → PII mask, **policy checks**, rate limits, audit logs.

---

## 9) Calendar (10 weeks, outputs only)

- **W1:** MLflow wired on both; registry entries; public roadmap post.
- **W2:** CI posts eval summary; promote/rollback; draft Loom #1; 10 tailored apps.
- **W3:** vLLM path live; start load/cost runs; 10 warm intros; 2 coffee chats.
- **W4:** SLO‑gated CI; finalize Grafana; publish Post #1 (SLO‑gated CI).
- **W5:** Drift + A/B finalized; ImpactScore R²; record Looms; 10 more apps.
- **W6:** Minimal AWS slice + rollback Loom; Post #2 (requests‑per‑dollar).
- **W7:** Publish lite repos; 2 screens secured; weekly mocks.
- **W8–10:** Referral sprint; 2–3 live interviews; contract lane. Finals + offers.

---

## 10) Interview prep

Design a 1k QPS RAG/LLM service; cost vs latency trade‑offs; when vLLM vs API; drift detection; A/B without peeking; guardrails (prompt‑injection, PII, policy, rate limits); incident story (alert→diagnose→mitigate→postmortem).

---

## 11) Negotiation checklist

Base/bonus/equity + LLM budget + GPU access + remote hours + on‑call. Anchor high with Proof Pack. Bundle (salary+equity+learning+conferences). Contractors: rate card + SOW with milestones & acceptance.

---

## 12) Payments & legal (company‑only)

- Contract with **UK LTD**. Currency USD/EUR/GBP. **Net 15**.
- **Wise Business** (primary), **Revolut Business** (backup), **Payoneer Business** only if in LTD name.
- Stripe Invoicing only if needed. **W‑8BEN‑E** for US. Attach: **How_to_Pay_Me_OnePager_COMPANY_ONLY.md**, **Contract_Rate_Card.md**.

---

## 13) Monorepo & guardrails

- Layout: `/infra`, `/threads_agent`, `/roi_agent`, `/achievement_collector`, `/techdoc_generator`, `/common`, `/docs`, `/tests`.
- Trunk‑based; short branches; protected main; CODEOWNERS; pre‑commit; feature flags; canary + rollback; CI path filters; **SLO gates**; prompt safety & PII scans on every PR.
- Lite demos must run in **<5 min** with Docker Compose + fake data.

---

## 14) Risks & mitigations

Remote‑only policy → keep EU/UK + contract lane.
Long funnels → 8–10 apps/week + warm intros + weekly posts.
Lifecycle gaps → close MLflow/evals/drift in W1–W3.
Cloud light → ship minimal AWS slice + Loom.
Ads policy risk → policy checks, audit logs, safe‑pause.
Repo complexity → lead with lite demos + crisp READMEs.

---

## 15) What to stop

Features that don’t feed a demo/metric. Research‑title chasing. Extra microservices.

---

## 16) One‑page CV bullets (AI‑tuned)

- Built and operated **two LLM platforms** on K8s/ECS with CI/CD, observability, **multi‑model routing**, and graceful degradation.
- Integrated **MLflow registry** with automated evals, **SLO‑gated releases**, and minute‑level rollback.
- Cut **token cost 30–50%** using **vLLM** while holding **p95** under target.
- Implemented **drift** signals and **A/B** testing (sequential decisioning).
- Deployed a **minimal AWS** slice (IaC, IAM least‑privilege), with runbooks and alerts.
- For ads: BLIP‑2 creative analysis, policy‑safe automation (pause/resume), daily rollups, Slack→Linear automation.
- Leadership: led teams (3–4 devs), CI/CD ownership, raised App Store ratings, shipped 50M+‑download apps (transfer this rigor to LLM SLOs).

---

## 17) Seven‑day starter checklist

- MLflow registry live in both projects; 2 versions; rollback tested.
- CI comment with eval summary; **SLO gates** (p95/error/token‑cost Δ).
- vLLM integrated for one step; start load + cost runs.
- Grafana board finalized; screenshots saved.
- Threads‑Agent‑lite & ROI‑Agent‑lite skeletons published.
- Draft Looms; schedule recording.
- 10 tailored applications with Proof Pack links.

---

## 18) Mini‑briefs & outreach scripts

- Use `/mini_briefs/brief_template.md` + examples to craft 3–5 briefs/week (AI infra, Adtech, Productivity SaaS).
- **Script A:** “Built two LLM platforms with MLflow registry, SLO‑gated CI, and vLLM cost cuts. Here’s a 2‑minute demo + cost table. Happy to walk you through deploy/observe/rollback.”
- **Script B:** “Scaling GenAI features? My playbook reduces token cost 30–50% at steady p95, adds drift+A/B. Screenshots + runbook inside.”

---

## 19) Tiny public dataset & eval harness

- Data: `/data/tiny_impactscores_public.csv`
- ImpactScore eval: `/evals/eval_impactscore.py` prints weights + **R²**
- Latency/cost delta: `/evals/eval_latency_cost_sample.py` reads `results.json` and computes Δp95% and Δcost%
- Publish in demo repo so anyone can re‑run numbers.

---

## 20) Optional AWS Bedrock add‑on (1–2 days max)

- Enable 1 model; create **Guardrails** (PII + safe topics); build a tiny **Knowledge Base** on S3; run 5–10 RAG queries; wire CloudWatch p95/error alarms.
- Add one Loom (“Guardrails + KB + alarms”) and a row in your cost/latency table (**Bedrock vs vLLM**). Use if employer base is AWS‑heavy.

---

## 21) File index

- AI_JOB_STRATEGY_v11.md (this file)
- How_to_Pay_Me_OnePager_COMPANY_ONLY.md · Contract_Rate_Card.md
- /mini_briefs/ (template + 3 examples)
- /data/tiny_impactscores_public.csv
- /evals/eval_impactscore.py · /evals/eval_latency_cost_sample.py

---

**Principle:** If something takes >1 week, ship a thinner slice that still yields a **screenshot, table, or 2‑minute Loom**. Outcomes, not promises.
