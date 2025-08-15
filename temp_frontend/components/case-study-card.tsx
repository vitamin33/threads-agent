import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Calendar,
  DollarSign,
  Clock,
  TrendingUp,
  ExternalLink,
} from 'lucide-react';
import type { CaseStudy } from '@/lib/case-studies';

interface CaseStudyCardProps {
  caseStudy: CaseStudy;
}

export function CaseStudyCard({ caseStudy }: CaseStudyCardProps) {
  const formatCurrency = (value: number): string => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  const getImpactColor = (score: number): string => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 80) return 'text-blue-600 bg-blue-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  return (
    <Card className="h-full hover:shadow-lg transition-shadow group">
      {/* Cover Image */}
      <div className="relative h-48 overflow-hidden bg-gradient-to-br from-primary/10 to-secondary/10 rounded-t-lg">
        <div className="absolute top-4 right-4">
          {caseStudy.featured && (
            <Badge className="bg-primary text-primary-foreground">
              Featured
            </Badge>
          )}
        </div>
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 rounded-lg bg-primary/20 flex items-center justify-center mb-2">
              <TrendingUp className="h-8 w-8 text-primary" />
            </div>
            <Badge variant="outline" className="text-xs">
              {caseStudy.category}
            </Badge>
          </div>
        </div>
      </div>

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between mb-2">
          <CardTitle className="text-lg font-semibold leading-tight line-clamp-2">
            {caseStudy.title}
          </CardTitle>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-2">
          <div
            className={`flex items-center gap-1 text-sm px-2 py-1 rounded ${getImpactColor(caseStudy.impact_score)}`}
          >
            <TrendingUp className="h-3 w-3" />
            <span className="font-medium">{caseStudy.impact_score}/100</span>
          </div>

          <div className="flex items-center gap-1 text-sm text-green-600 bg-green-50 px-2 py-1 rounded">
            <DollarSign className="h-3 w-3" />
            <span className="font-medium">
              {formatCurrency(caseStudy.business_value)}
            </span>
          </div>

          <div className="flex items-center gap-1 text-sm text-orange-600 bg-orange-50 px-2 py-1 rounded">
            <Clock className="h-3 w-3" />
            <span className="font-medium">{caseStudy.duration_hours}h</span>
          </div>

          <div className="flex items-center gap-1 text-sm text-purple-600 bg-purple-50 px-2 py-1 rounded">
            <Calendar className="h-3 w-3" />
            <span className="font-medium">{caseStudy.readingTime}min read</span>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Summary */}
        <p className="text-sm text-muted-foreground line-clamp-3">
          {caseStudy.summary}
        </p>

        {/* Tech Stack */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Tech Stack
          </h4>
          <div className="flex flex-wrap gap-1">
            {caseStudy.tech.slice(0, 4).map(tech => (
              <Badge key={tech} variant="secondary" className="text-xs">
                {tech}
              </Badge>
            ))}
            {caseStudy.tech.length > 4 && (
              <Badge variant="secondary" className="text-xs">
                +{caseStudy.tech.length - 4}
              </Badge>
            )}
          </div>
        </div>

        {/* Key Outcomes */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
            Key Outcomes
          </h4>
          <ul className="space-y-1">
            {caseStudy.outcomes.slice(0, 3).map((outcome, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                <span className="line-clamp-1">{outcome}</span>
              </li>
            ))}
            {caseStudy.outcomes.length > 3 && (
              <li className="text-xs text-muted-foreground">
                +{caseStudy.outcomes.length - 3} more outcomes
              </li>
            )}
          </ul>
        </div>

        {/* Links */}
        <div className="flex gap-2 pt-2">
          <Button size="sm" className="flex-1" asChild>
            <a href={caseStudy.url} className="flex items-center gap-2">
              View Details
            </a>
          </Button>

          {caseStudy.links.repo && (
            <Button variant="outline" size="sm" asChild>
              <a
                href={caseStudy.links.repo}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                Code
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
