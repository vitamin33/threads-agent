'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Download, Mail, MapPin, Globe, Phone } from 'lucide-react';

export default function ResumePage() {
  const handlePrintResume = () => {
    window.print();
  };

  return (
    <>
      <div className="container max-w-4xl py-8">
        {/* Print/Download Controls */}
        <div className="no-print mb-8 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Resume</h1>
          <Button onClick={handlePrintResume} className="gap-2">
            <Download className="h-4 w-4" />
            Download PDF
          </Button>
        </div>

        {/* Resume Content */}
        <div className="resume-content">
          {/* Header */}
          <header className="text-center mb-8">
            <h1 className="text-3xl font-bold mb-2">Vitalii Serbyn</h1>
            <h2 className="text-xl text-muted-foreground mb-4">
              AI Platform / MLOps Engineer
            </h2>
            <div className="flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Mail className="h-4 w-4" />
                serbyn.vitalii@gmail.com
              </span>
              <span className="flex items-center gap-1">
                <MapPin className="h-4 w-4" />
                Kyiv, Ukraine · Remote only · UK LTD for contracting
              </span>
              <span className="flex items-center gap-1">
                <Globe className="h-4 w-4" />
                serbyn.pro
              </span>
            </div>
          </header>

          {/* Professional Summary */}
          <section className="mb-8 page-break-inside-avoid">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Professional Summary
            </h3>
            <p className="text-sm leading-relaxed">
              Senior engineer with 12+ years shipping production systems in
              mobile, web, and cloud. I design and run reliable LLM services
              with clear SLOs, CI/CD, MLflow registries, cost controls, and real
              observability. I have led small teams, owned release trains, and I
              bring that discipline to building and operating AI platforms that
              are easy to deploy, measure, and roll back.
            </p>
          </section>

          {/* Technical Skills */}
          <section className="mb-8 page-break-inside-avoid">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Technical Skills
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h4 className="font-medium mb-2">
                  LLM & GenAI (Current Focus)
                </h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">LangChain/LangGraph</Badge>
                  <Badge variant="secondary">vLLM</Badge>
                  <Badge variant="secondary">OpenAI API</Badge>
                  <Badge variant="secondary">Ollama</Badge>
                  <Badge variant="secondary">BLIP-2</Badge>
                  <Badge variant="secondary">RAG</Badge>
                  <Badge variant="secondary">Hybrid Retrieval</Badge>
                </div>

                <h4 className="font-medium mb-2">
                  MLOps & Platform (Learning)
                </h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">MLflow</Badge>
                  <Badge variant="secondary">SLO-gated CI</Badge>
                  <Badge variant="secondary">A/B Evaluation</Badge>
                  <Badge variant="secondary">Experiment Tracking</Badge>
                  <Badge variant="secondary">Model Registry</Badge>
                  <Badge variant="secondary">Canary Deployment</Badge>
                </div>

                <h4 className="font-medium mb-2">Backend & Data (12+ years)</h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">Python</Badge>
                  <Badge variant="secondary">FastAPI</Badge>
                  <Badge variant="secondary">Node.js/NestJS</Badge>
                  <Badge variant="secondary">Celery</Badge>
                  <Badge variant="secondary">PostgreSQL</Badge>
                  <Badge variant="secondary">Redis</Badge>
                  <Badge variant="secondary">RabbitMQ</Badge>
                  <Badge variant="secondary">Qdrant</Badge>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">
                  Cloud & Infrastructure (Production)
                </h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">Kubernetes</Badge>
                  <Badge variant="secondary">Docker</Badge>
                  <Badge variant="secondary">AWS ECS/EKS</Badge>
                  <Badge variant="secondary">GCP/GKE</Badge>
                  <Badge variant="secondary">GitHub Actions</Badge>
                  <Badge variant="secondary">Terraform basics</Badge>
                </div>

                <h4 className="font-medium mb-2">
                  Observability & Ops (Expert)
                </h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">Prometheus</Badge>
                  <Badge variant="secondary">Grafana</Badge>
                  <Badge variant="secondary">Jaeger</Badge>
                  <Badge variant="secondary">Sentry</Badge>
                  <Badge variant="secondary">CloudWatch</Badge>
                  <Badge variant="secondary">PagerDuty</Badge>
                </div>

                <h4 className="font-medium mb-2">Frontend & Mobile</h4>
                <div className="flex flex-wrap gap-1 mb-3">
                  <Badge variant="secondary">Flutter</Badge>
                  <Badge variant="secondary">Android/Kotlin</Badge>
                  <Badge variant="secondary">React basics</Badge>
                </div>
              </div>
            </div>
          </section>

          {/* Professional Experience */}
          <section className="mb-8">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Professional Experience
            </h3>

            {/* Experience 1 */}
            <div className="mb-6 page-break-inside-avoid">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium">AI Platform / MLOps Engineer</h4>
                  <p className="text-sm text-muted-foreground">
                    Easelect LTD • Remote
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">
                  2023 - Present
                </span>
              </div>
              <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                <li>
                  Built Threads-Agent GenAI platform with MLflow registry,
                  SLO-gated CI, and production observability
                </li>
                <li>
                  Implemented ROI-Agent for automated media buying with
                  multimodal pipeline (BLIP-2 + LLM analysis)
                </li>
                <li>
                  Created Achievement Collector for PR impact analysis and
                  automated portfolio generation
                </li>
                <li>
                  Developed reliable LLM services with clear SLOs, cost
                  controls, and real observability
                </li>
                <li>
                  Applied production discipline to AI platforms: explicit SLOs,
                  fast rollback, cost budgets
                </li>
              </ul>
            </div>

            {/* Experience 2 */}
            <div className="mb-6 page-break-inside-avoid">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium">Senior/Lead Engineer</h4>
                  <p className="text-sm text-muted-foreground">
                    EPAM, GlobalLogic, Startups • Remote/Hybrid
                  </p>
                </div>
                <span className="text-sm text-muted-foreground">
                  2013 - 2023
                </span>
              </div>
              <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                <li>
                  Led teams of 3–4 engineers, owned release trains with 99.5+
                  uptime for mobile apps (5M+ MAU)
                </li>
                <li>
                  Optimized backend APIs serving 1M+ requests/day with p95
                  latency &lt;200ms (Redis caching, query optimization)
                </li>
                <li>
                  Implemented A/B testing frameworks processing 100k+ events/day
                  for user behavior analysis
                </li>
                <li>
                  Built event-driven architectures with message queues handling
                  50k+ messages/min peak load
                </li>
                <li>
                  Established monitoring with Prometheus/Grafana: 15+ custom
                  metrics, alert rules, SLA tracking
                </li>
                <li>
                  Reduced deployment time from 45min to 3min using Docker +
                  Kubernetes + automated rollback
                </li>
              </ul>
              <p className="text-xs text-muted-foreground mt-2 italic">
                <strong>AI Relevance:</strong> These same patterns apply to LLM
                services: p95 latency SLOs, request/response caching, event
                processing for model inputs, monitoring for drift detection, and
                fast rollback for model deployments.
              </p>
            </div>
          </section>

          {/* Key Projects */}
          <section className="mb-8">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Key Projects
            </h3>

            <div className="space-y-4">
              <div className="page-break-inside-avoid">
                <h4 className="font-medium">
                  Threads-Agent — GenAI Content Platform
                </h4>
                <p className="text-sm text-muted-foreground mb-2">
                  LangGraph • MLflow • Kubernetes • Prometheus • 2024 • Personal
                  R&D
                </p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>
                    Multi-service system: persona runtime, optimizer service,
                    publishing adapters
                  </li>
                  <li>
                    MLflow model registry with evaluation jobs tied to CI for
                    automated quality gates
                  </li>
                  <li>
                    SLO-gated deployments on p95 latency, error rate, and
                    token-cost deltas
                  </li>
                  <li>
                    Full observability stack: Prometheus metrics, Grafana
                    dashboards, Jaeger tracing
                  </li>
                </ul>
              </div>

              <div className="page-break-inside-avoid">
                <h4 className="font-medium">
                  ROI-Agent — Media Buyer Automation
                </h4>
                <p className="text-sm text-muted-foreground mb-2">
                  BLIP-2 • Ollama • Meta Ads API • Celery • 2024 • Personal R&D
                </p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>
                    Multimodal pipeline: BLIP-2 for creative captions, LLM
                    analysis for copy variants
                  </li>
                  <li>
                    Hybrid inference: local Ollama (Mixtral) with OpenAI
                    fallback and structured output
                  </li>
                  <li>
                    A/B testing with sequential decision rules, performance
                    rollups, policy guardrails
                  </li>
                  <li>
                    Integrations: Facebook Graph API, Shopify webhooks, Slack to
                    Linear automation
                  </li>
                </ul>
              </div>

              <div className="page-break-inside-avoid">
                <h4 className="font-medium">
                  Achievement Collector — Portfolio Automation
                </h4>
                <p className="text-sm text-muted-foreground mb-2">
                  GitHub API • Impact Analysis • Portfolio Generation • 2024 •
                  Personal R&D
                </p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>
                    GitHub PR analysis extracting technical metrics and
                    generating ImpactScores
                  </li>
                  <li>
                    Automated portfolio generation from development activity and
                    MLflow experiments
                  </li>
                  <li>
                    CI integration for consistent reporting and resume bullet
                    generation
                  </li>
                </ul>
              </div>

              <div className="page-break-inside-avoid">
                <h4 className="font-medium">
                  High-Traffic Mobile Backend Infrastructure
                </h4>
                <p className="text-sm text-muted-foreground mb-2">
                  Node.js • PostgreSQL • Redis • Kubernetes • 2018-2022 •
                  EPAM/GlobalLogic
                </p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>
                    API gateway handling 1M+ requests/day with circuit breakers
                    and rate limiting
                  </li>
                  <li>
                    Real-time event processing: 100k+ events/day through Redis
                    Streams and message queues
                  </li>
                  <li>
                    Database optimization: query performance tuning reducing p95
                    response time from 800ms to 120ms
                  </li>
                  <li>
                    Monitoring implementation: 20+ custom Prometheus metrics
                    with Grafana dashboards and PagerDuty alerts
                  </li>
                </ul>
              </div>
            </div>
          </section>

          {/* Education */}
          <section className="mb-8 page-break-inside-avoid">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Education
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <div>
                  <h4 className="font-medium">M.Sc. in Computer Science</h4>
                  <p className="text-muted-foreground">
                    V. N. Karazin Kharkiv National University
                  </p>
                </div>
                <span className="text-muted-foreground">2009 - 2011</span>
              </div>
              <div className="flex justify-between">
                <div>
                  <h4 className="font-medium">
                    Software Engineering Management
                  </h4>
                  <p className="text-muted-foreground">EPAM School</p>
                </div>
                <span className="text-muted-foreground">2019</span>
              </div>
            </div>
          </section>

          {/* Business Setup & Legal */}
          <section className="mb-8 page-break-inside-avoid">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Business Setup & Legal
            </h3>
            <div className="space-y-2 text-sm">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">Contracting</h4>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>UK LTD available for contracting</li>
                    <li>Comfortable with W-8BEN-E for US clients</li>
                    <li>Professional indemnity insurance</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Payments</h4>
                  <ul className="list-disc list-inside space-y-1 ml-4">
                    <li>Wise Business or Revolut Business</li>
                    <li>Crypto: USDC/USDT (ERC-20, SOL, TRX)</li>
                    <li>Invoices in USD, EUR, or GBP</li>
                    <li>Standard contracting terms available</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Languages */}
          <section className="mb-8 page-break-inside-avoid">
            <h3 className="text-lg font-semibold mb-3 border-b pb-1">
              Languages
            </h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>English: Fluent</div>
              <div>Ukrainian: Native</div>
              <div>Russian: Native</div>
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
