import { Hero } from '@/components/hero';
import { ProofPack } from '@/components/proof-pack';
import { Services } from '@/components/services';
import { CaseCard } from '@/components/case-card';
import { Contact } from '@/components/contact';
import { AchievementsLive } from '@/components/achievements-live';

export default function Home() {
  // Sample case studies data
  const featuredCases = [
    {
      title: 'E-commerce LLM Personalization Engine',
      summary:
        'Built a real-time product recommendation system using fine-tuned LLMs and vector search, improving conversion rates and customer engagement.',
      techStack: ['Python', 'vLLM', 'Pinecone', 'FastAPI', 'Redis'],
      outcomes: [
        '23% increase in conversion rate',
        '45% reduction in cart abandonment',
        '60% faster response times',
        'Scaled to 1M+ daily users',
      ],
      link: '/case-studies/ecommerce-personalization',
    },
    {
      title: 'Financial RAG System for Compliance',
      summary:
        'Developed a regulatory document analysis system using RAG architecture to automate compliance checking and reporting.',
      techStack: ['LangChain', 'OpenAI', 'Elasticsearch', 'Docker', 'AWS'],
      outcomes: [
        '80% reduction in manual review time',
        '99.5% accuracy in compliance detection',
        'Processed 10K+ documents daily',
        'SOC 2 compliant deployment',
      ],
      link: '/case-studies/financial-rag',
    },
    {
      title: 'MLOps Pipeline for Model Lifecycle',
      summary:
        'Implemented end-to-end MLOps pipeline with automated retraining, A/B testing, and deployment for a SaaS platform.',
      techStack: [
        'MLflow',
        'Kubernetes',
        'GitHub Actions',
        'Prometheus',
        'Grafana',
      ],
      outcomes: [
        '90% reduction in deployment time',
        'Zero-downtime model updates',
        'Automated rollback in <2 minutes',
        '99.9% system uptime',
      ],
      link: '/case-studies/mlops-pipeline',
    },
  ];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <Hero />

      {/* Proof Pack Section */}
      <ProofPack />

      {/* Services Section */}
      <Services />

      {/* Featured Case Studies Section */}
      <section className="py-16 sm:py-24">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Featured Case Studies
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Real-world implementations with measurable business impact
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {featuredCases.map((caseStudy, index) => (
              <CaseCard key={index} {...caseStudy} />
            ))}
          </div>

          <div className="mt-12 text-center">
            <p className="text-muted-foreground mb-4 max-w-2xl mx-auto">
              Want to see more detailed case studies and technical deep-dives?
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button className="btn btn-secondary">
                <a href="/about">View Experience</a>
              </button>
              <button className="btn btn-primary">
                <a href="#contact">Discuss Your Project</a>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Live Achievements Section */}
      <section className="py-16 sm:py-24 bg-muted/30">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Recent Achievements
            </h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Live data showcasing quantified business impact and technical
              expertise
            </p>
          </div>

          <AchievementsLive
            showHeroStats={true}
            showFilters={true}
            limit={6}
            featuredOnly={true}
          />

          <div className="mt-12 text-center">
            <p className="text-muted-foreground mb-4 max-w-2xl mx-auto">
              Real-time achievements pulled from GitHub PRs and deployment
              metrics
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button className="btn btn-secondary">
                <a href="/achievements">View All Achievements</a>
              </button>
              <button className="btn btn-primary">
                <a href="/api/resume">Download Resume JSON</a>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <Contact />
    </div>
  );
}
