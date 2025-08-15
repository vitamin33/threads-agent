import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ServiceCardProps {
  title: string;
  description: string;
  features: string[];
  icon: React.ReactNode;
  href: string;
}

function ServiceCard({
  title,
  description,
  features,
  icon,
  href,
}: ServiceCardProps) {
  return (
    <Card className="relative h-full transition-all duration-300 hover:shadow-lg border-border/50">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
            {icon}
          </div>
          <CardTitle className="text-xl">{title}</CardTitle>
        </div>
        <p className="text-muted-foreground">{description}</p>
      </CardHeader>
      <CardContent className="pt-0">
        <ul className="space-y-2 mb-6">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start gap-2 text-sm">
              <div className="h-1.5 w-1.5 rounded-full bg-primary mt-2 flex-shrink-0"></div>
              <span>{feature}</span>
            </li>
          ))}
        </ul>
        <Button variant="outline" className="w-full" asChild>
          <a href={href}>Learn more</a>
        </Button>
      </CardContent>
    </Card>
  );
}

export function Services() {
  const services = [
    {
      title: 'LLM Infrastructure & RAG',
      description:
        'End-to-end LLM deployment with RAG systems, vector databases, and production monitoring.',
      features: [
        'vLLM and TGI deployment optimization',
        'Vector database setup (Pinecone, Weaviate, Chroma)',
        'RAG pipeline design and evaluation',
        'Embedding model fine-tuning',
        'Retrieval quality monitoring',
        'Cost optimization strategies',
      ],
      href: '#contact',
      icon: (
        <svg
          className="h-6 w-6 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
      ),
    },
    {
      title: 'MLOps & Lifecycle',
      description:
        'Complete ML lifecycle management with automated training, evaluation, and deployment pipelines.',
      features: [
        'MLflow experiment tracking and model registry',
        'Automated retraining pipelines',
        'Model performance monitoring',
        'A/B testing infrastructure',
        'SLO-based deployment gates',
        'Rollback and canary deployment strategies',
      ],
      href: '#contact',
      icon: (
        <svg
          className="h-6 w-6 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      ),
    },
    {
      title: 'GenAI for Marketing & E-commerce',
      description:
        'Custom GenAI solutions for content generation, personalization, and customer experience optimization.',
      features: [
        'Content generation and SEO optimization',
        'Product description automation',
        'Customer support chatbots',
        'Personalization engines',
        'A/B testing for AI-generated content',
        'ROI measurement and optimization',
      ],
      href: '#contact',
      icon: (
        <svg
          className="h-6 w-6 text-primary"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
      ),
    },
  ];

  return (
    <section id="services" className="py-16 sm:py-24 bg-muted/30">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Services
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Specialized AI/ML engineering services with proven production
            experience
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {services.map((service, index) => (
            <ServiceCard key={index} {...service} />
          ))}
        </div>

        {/* Call-to-Action */}
        <div className="mt-12 text-center">
          <p className="text-muted-foreground mb-4 max-w-2xl mx-auto">
            Need a custom solution? Let&apos;s discuss your specific
            requirements.
          </p>
          <Button size="lg" asChild>
            <a href="#contact">Get Started</a>
          </Button>
        </div>
      </div>
    </section>
  );
}
