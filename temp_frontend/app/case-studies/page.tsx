import { getAllCaseStudies, getCaseStudyStats } from '@/lib/case-studies';
import { CaseStudyCard } from '@/components/case-study-card';
import { StatsOverview } from '@/components/stats-overview';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata.caseStudies();

export default function CaseStudiesPage() {
  const caseStudies = getAllCaseStudies();
  const stats = getCaseStudyStats();

  const featuredStudies = caseStudies.filter(study => study.featured);
  const categories = ['all', 'infrastructure', 'optimization', 'feature'];

  return (
    <div className="min-h-screen py-16">
      <div className="container">
        {/* Header */}
        <div className="mx-auto max-w-3xl text-center mb-16">
          <h1 className="text-4xl font-bold tracking-tight mb-6">
            Case Studies
          </h1>
          <p className="text-xl text-muted-foreground leading-8">
            Deep-dive technical implementations with quantified business impact,
            live metrics, and evidence from production systems.
          </p>
        </div>

        {/* Stats Overview */}
        <StatsOverview
          totalCases={stats.totalCases}
          totalValue={stats.totalValue}
          avgImpact={stats.avgImpact}
          totalHours={stats.totalHours}
          avgROI={stats.avgROI}
          categories={stats.categories}
        />

        {/* Featured Case Studies */}
        {featuredStudies.length > 0 && (
          <section className="mb-16">
            <h2 className="text-2xl font-bold mb-8 text-center">
              Featured Case Studies
            </h2>
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {featuredStudies.map(caseStudy => (
                <CaseStudyCard key={caseStudy.slug} caseStudy={caseStudy} />
              ))}
            </div>
          </section>
        )}

        {/* All Case Studies */}
        <section className="mb-16">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold">All Case Studies</h2>
            <div className="flex gap-2">
              {categories.map(category => (
                <Badge
                  key={category}
                  variant="secondary"
                  className="capitalize"
                >
                  {category === 'all'
                    ? `All (${caseStudies.length})`
                    : category}
                </Badge>
              ))}
            </div>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {caseStudies.map(caseStudy => (
              <CaseStudyCard key={caseStudy.slug} caseStudy={caseStudy} />
            ))}
          </div>
        </section>

        {/* Call to Action */}
        <section className="text-center">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle>Interested in Similar Results?</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-6">
                These case studies represent real implementations with
                measurable business impact. Let&apos;s discuss how similar
                approaches can benefit your organization.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" asChild>
                  <a href="#contact">Discuss Your Project</a>
                </Button>
                <Button variant="outline" size="lg" asChild>
                  <a href="/resume">View Technical Background</a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
