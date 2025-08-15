import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata.about();

export default function AboutPage() {
  const achievements = [
    {
      metric: '10M+',
      description: 'Requests/month processed by deployed systems',
    },
    {
      metric: '45%',
      description: 'Average cost reduction achieved for clients',
    },
    {
      metric: '99.9%',
      description: 'Uptime maintained across production deployments',
    },
    {
      metric: '<2min',
      description: 'Model rollback time in production',
    },
  ];

  const experience = [
    {
      title: 'LLM Production Systems',
      description:
        'Deployed and scaled large language models serving millions of users with sub-300ms p95 latency',
    },
    {
      title: 'MLOps Infrastructure',
      description:
        'Built end-to-end ML pipelines with automated training, evaluation, and deployment using MLflow',
    },
    {
      title: 'Cost Optimization',
      description:
        'Reduced token costs by 30-50% through vLLM deployment and intelligent caching strategies',
    },
    {
      title: 'Enterprise Integration',
      description:
        'Implemented RAG systems and AI solutions for Fortune 500 companies with SOC 2 compliance',
    },
  ];

  return (
    <div className="min-h-screen py-16">
      <div className="container">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <h1 className="text-4xl font-bold tracking-tight mb-6">About</h1>
          <div className="prose prose-lg mx-auto text-muted-foreground">
            <p className="text-xl leading-8">
              Senior engineer with 12+ years shipping production systems in
              mobile, web, and cloud. I design and run reliable LLM services
              with clear SLOs, CI/CD, MLflow registries, cost controls, and real
              observability.
            </p>
            <p className="text-lg leading-7 mt-6">
              Currently building personal R&D projects to learn enterprise MLOps
              patterns: Threads-Agent (GenAI platform), ROI-Agent (multimodal
              automation), and Achievement Collector. I bring production
              discipline from EPAM/GlobalLogic to AI platforms.
            </p>
          </div>
        </div>

        {/* Key Achievements */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-center mb-8">
            Key Achievements
          </h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {achievements.map((achievement, index) => (
              <Card key={index} className="text-center">
                <CardContent className="pt-6">
                  <div className="text-3xl font-bold text-primary mb-2">
                    {achievement.metric}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {achievement.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Experience Highlights */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-center mb-8">
            Experience Highlights
          </h2>
          <div className="grid gap-6 md:grid-cols-2">
            {experience.map((item, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{item.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {item.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Technical Expertise */}
        <section className="mb-16">
          <Card className="max-w-4xl mx-auto">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">Technical Expertise</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-3">
                <div>
                  <h3 className="font-semibold mb-3 text-primary">
                    LLM Deployment
                  </h3>
                  <ul className="text-sm space-y-1">
                    <li>• vLLM, TGI, Ollama</li>
                    <li>• Model quantization & optimization</li>
                    <li>• Multi-GPU scaling</li>
                    <li>• Inference cost analysis</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-3 text-primary">
                    MLOps & Infrastructure
                  </h3>
                  <ul className="text-sm space-y-1">
                    <li>• MLflow, Kubeflow, DVC</li>
                    <li>• Kubernetes, Docker</li>
                    <li>• CI/CD with GitHub Actions</li>
                    <li>• Monitoring with Prometheus/Grafana</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-semibold mb-3 text-primary">
                    AI/ML Frameworks
                  </h3>
                  <ul className="text-sm space-y-1">
                    <li>• PyTorch, HuggingFace</li>
                    <li>• LangChain, LlamaIndex</li>
                    <li>• Vector databases (Pinecone, Weaviate)</li>
                    <li>• FastAPI, Redis, PostgreSQL</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Call to Action */}
        <section className="text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to Work Together?</h2>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Download my detailed resume or get in touch to discuss how I can
            help optimize your AI/ML systems for production scale.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" asChild>
              <a href="/resume" className="flex items-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Download Resume
              </a>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#contact">Get in Touch</a>
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}
