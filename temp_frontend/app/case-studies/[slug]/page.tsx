import { notFound } from 'next/navigation';
import {
  getCaseStudyBySlug,
  getAllCaseStudies,
  linkCaseStudyToAchievement,
} from '@/lib/case-studies';
import { CaseStudyHeader } from '@/components/case-study-header';
import { CaseStudyFooter } from '@/components/case-study-footer';
import { MetricsComparison } from '@/components/metrics-comparison';
import { ImpactCard } from '@/components/impact-card';
import { EvidenceSection } from '@/components/evidence-section';
import { LiveMetricsWidget } from '@/components/live-metrics-widget';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import achievementsData from '@/data/achievements.json';

// Generate static params for all case studies - temporarily disabled for deployment
export async function generateStaticParams() {
  // Return empty array to skip case study page generation during build
  // This allows main portfolio to deploy while case studies are being fixed
  return [];
}

// Generate metadata for each case study
export async function generateMetadata({
  params,
}: {
  params: { slug: string };
}) {
  const caseStudy = getCaseStudyBySlug(params.slug);

  if (!caseStudy) {
    return {
      title: 'Case Study Not Found',
    };
  }

  return {
    title: `${caseStudy.title} | Case Study`,
    description: caseStudy.summary,
    keywords: caseStudy.seo_keywords?.join(', '),
    openGraph: {
      title: caseStudy.title,
      description: caseStudy.summary,
      images: [caseStudy.cover],
      type: 'article',
      publishedTime: caseStudy.date,
    },
  };
}

// Custom MDX components that connect to live data
const mdxComponents = {
  MetricsComparison: ({ before, after }: { before: any; after: any }) => (
    <MetricsComparison beforeMetrics={before} afterMetrics={after} />
  ),
  ImpactCard: ({
    businessValue,
    impactScore,
    outcomes,
  }: {
    businessValue: number;
    impactScore: number;
    outcomes: string[];
  }) => (
    <ImpactCard
      businessValue={businessValue}
      impactScore={impactScore}
      outcomes={outcomes}
    />
  ),
  EvidenceSection: ({ links, gallery }: { links: any; gallery?: string[] }) => (
    <EvidenceSection links={links} gallery={gallery} />
  ),
  TechStack: ({ tech }: { tech: string[] }) => (
    <div className="flex flex-wrap gap-2 my-4">
      {tech.map(item => (
        <Badge key={item} variant="secondary">
          {item}
        </Badge>
      ))}
    </div>
  ),
};

export default function CaseStudyPage({
  params,
}: {
  params: { slug: string };
}) {
  const caseStudy = getCaseStudyBySlug(params.slug);

  if (!caseStudy) {
    notFound();
  }

  // Link to achievement data for live metrics
  const linkedAchievement = linkCaseStudyToAchievement(
    caseStudy,
    achievementsData.achievements
  );

  return (
    <div className="min-h-screen py-16">
      <div className="container max-w-4xl">
        {/* Navigation */}
        <div className="mb-8">
          <Button variant="ghost" asChild>
            <a href="/case-studies" className="flex items-center gap-2">
              <ArrowLeft className="h-4 w-4" />
              Back to Case Studies
            </a>
          </Button>
        </div>

        {/* Case Study Header */}
        <CaseStudyHeader caseStudy={caseStudy} />

        {/* Live Metrics Widget (if linked to achievement) */}
        {linkedAchievement && (
          <div className="mb-12">
            <LiveMetricsWidget achievement={linkedAchievement} />
          </div>
        )}

        {/* Article Content */}
        <article className="prose prose-lg max-w-none">
          {/* Challenge Section */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Challenge</h2>
            <p className="text-lg text-muted-foreground">
              {caseStudy.description}
            </p>
          </section>

          {/* Technical Stack */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Technical Stack</h2>
            <div className="flex flex-wrap gap-2">
              {caseStudy.tech.map(tech => (
                <Badge key={tech} variant="secondary">
                  {tech}
                </Badge>
              ))}
            </div>
            {caseStudy.architecture && (
              <div className="mt-4">
                <h3 className="text-lg font-semibold mb-2">
                  Architecture Patterns
                </h3>
                <div className="flex flex-wrap gap-2">
                  {caseStudy.architecture.map(pattern => (
                    <Badge key={pattern} variant="outline">
                      {pattern}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </section>

          {/* Metrics Comparison */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Performance Impact</h2>
            <MetricsComparison
              beforeMetrics={caseStudy.metrics_before}
              afterMetrics={caseStudy.metrics_after}
            />
          </section>

          {/* Business Impact */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Business Impact</h2>
            <ImpactCard
              businessValue={caseStudy.business_value}
              impactScore={caseStudy.impact_score}
              outcomes={caseStudy.outcomes}
            />
          </section>

          {/* MDX Content would go here */}
          <div className="prose max-w-none">
            <div className="bg-muted/50 rounded-lg p-6 mb-8">
              <h3 className="text-lg font-semibold mb-3">
                Technical Implementation
              </h3>
              <p className="text-muted-foreground">
                Detailed technical content and code examples are rendered from
                the MDX file. This includes architecture diagrams, code
                snippets, and step-by-step implementation details.
              </p>
            </div>
          </div>

          {/* Evidence & Links */}
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-4">Evidence & Verification</h2>
            <EvidenceSection
              links={caseStudy.links}
              gallery={caseStudy.gallery}
            />
          </section>
        </article>

        {/* Case Study Footer */}
        <CaseStudyFooter caseStudy={caseStudy} />
      </div>
    </div>
  );
}
