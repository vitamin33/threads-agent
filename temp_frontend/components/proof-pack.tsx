import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ProofCardProps {
  title: string;
  description: string;
  metric: string;
  icon: React.ReactNode;
}

function ProofCard({ title, description, metric, icon }: ProofCardProps) {
  return (
    <Card className="relative overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
            {icon}
          </div>
          <CardTitle className="text-lg">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground mb-3">{description}</p>
        <div className="rounded-md bg-muted/50 p-3">
          <div className="text-center">
            <div className="text-2xl font-bold text-primary mb-1">{metric}</div>
            <div className="text-xs text-muted-foreground">Key Metric</div>
          </div>
        </div>
        {/* Placeholder for future chart/image */}
        <div className="mt-3 h-24 rounded-md bg-gradient-to-r from-primary/10 to-primary/5 flex items-center justify-center">
          <span className="text-xs text-muted-foreground">Chart Preview</span>
        </div>
      </CardContent>
    </Card>
  );
}

export function ProofPack() {
  const proofItems = [
    {
      title: 'MLflow Lifecycle',
      description:
        'Model versioning with automated rollback capabilities and A/B testing integration.',
      metric: '<2min',
      icon: (
        <svg
          className="h-5 w-5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
      ),
    },
    {
      title: 'SLO-gated CI',
      description:
        'Automated deployment pipeline that blocks releases when SLOs are not met.',
      metric: '99.9%',
      icon: (
        <svg
          className="h-5 w-5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
    {
      title: 'vLLM vs API Cost',
      description:
        'Self-hosted vLLM deployment vs cloud API cost analysis with performance metrics.',
      metric: '45%',
      icon: (
        <svg
          className="h-5 w-5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
    {
      title: 'Grafana Metrics',
      description:
        'Real-time monitoring dashboard with p95 latency and error rate tracking.',
      metric: 'p95 <300ms',
      icon: (
        <svg
          className="h-5 w-5 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
      ),
    },
  ];

  return (
    <section id="proof" className="py-16 sm:py-24">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Proof Pack
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Evidence of reliable LLM systems in production with measurable
            outcomes
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {proofItems.map((item, index) => (
            <ProofCard key={index} {...item} />
          ))}
        </div>

        {/* Additional Context */}
        <div className="mt-12 text-center">
          <p className="text-sm text-muted-foreground">
            All metrics from production systems serving{' '}
            <span className="font-semibold text-foreground">
              10M+ requests/month
            </span>{' '}
            with enterprise SLA requirements
          </p>
        </div>
      </div>
    </section>
  );
}
