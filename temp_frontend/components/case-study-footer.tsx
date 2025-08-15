import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ArrowRight, MessageCircle, Download } from 'lucide-react';
import type { CaseStudy } from '@/lib/case-studies';
import { getAllCaseStudies } from '@/lib/case-studies';

interface CaseStudyFooterProps {
  caseStudy: CaseStudy;
}

export function CaseStudyFooter({ caseStudy }: CaseStudyFooterProps) {
  const allCaseStudies = getAllCaseStudies();
  const currentIndex = allCaseStudies.findIndex(
    study => study.slug === caseStudy.slug
  );

  const prevStudy = currentIndex > 0 ? allCaseStudies[currentIndex - 1] : null;
  const nextStudy =
    currentIndex < allCaseStudies.length - 1
      ? allCaseStudies[currentIndex + 1]
      : null;

  return (
    <footer className="mt-16 space-y-8">
      {/* SEO Keywords */}
      {caseStudy.seo_keywords && caseStudy.seo_keywords.length > 0 && (
        <div>
          <h3 className="font-semibold mb-3">Related Technologies</h3>
          <div className="flex flex-wrap gap-2">
            {caseStudy.seo_keywords.map(keyword => (
              <Badge key={keyword} variant="outline" className="text-xs">
                {keyword}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Call to Action */}
      <Card className="bg-gradient-to-r from-primary/5 to-secondary/5">
        <CardHeader>
          <CardTitle className="text-center">
            Interested in Similar Results?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center text-muted-foreground mb-6">
            This case study demonstrates real-world implementation with
            quantified business impact. Let&apos;s discuss how similar
            approaches can benefit your organization.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="flex items-center gap-2" asChild>
              <a href="#contact">
                <MessageCircle className="h-4 w-4" />
                Discuss Your Project
              </a>
            </Button>
            <Button
              variant="outline"
              size="lg"
              className="flex items-center gap-2"
              asChild
            >
              <a href="/resume">
                <Download className="h-4 w-4" />
                View Technical Background
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Navigation to Other Case Studies */}
      <div className="grid gap-4 md:grid-cols-2">
        {prevStudy && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2">
                <ArrowLeft className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  Previous Case Study
                </span>
              </div>
              <h4 className="font-semibold mb-2 line-clamp-2">
                {prevStudy.title}
              </h4>
              <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                {prevStudy.summary}
              </p>
              <Button variant="outline" className="w-full" asChild>
                <a href={prevStudy.url}>Read Case Study</a>
              </Button>
            </CardContent>
          </Card>
        )}

        {nextStudy && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 mb-2 justify-end">
                <span className="text-sm text-muted-foreground">
                  Next Case Study
                </span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </div>
              <h4 className="font-semibold mb-2 line-clamp-2 text-right">
                {nextStudy.title}
              </h4>
              <p className="text-sm text-muted-foreground mb-4 line-clamp-2 text-right">
                {nextStudy.summary}
              </p>
              <Button variant="outline" className="w-full" asChild>
                <a href={nextStudy.url}>Read Case Study</a>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Back to All Case Studies */}
      <div className="text-center pt-8 border-t">
        <Button variant="ghost" asChild>
          <a href="/case-studies" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            View All Case Studies
          </a>
        </Button>
      </div>
    </footer>
  );
}
