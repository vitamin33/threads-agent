import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Calendar, Clock, DollarSign, TrendingUp } from 'lucide-react';
import type { CaseStudy } from '@/lib/case-studies';

interface CaseStudyHeaderProps {
  caseStudy: CaseStudy;
}

export function CaseStudyHeader({ caseStudy }: CaseStudyHeaderProps) {
  const formatCurrency = (value: number): string => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  const getImpactColor = (score: number): string => {
    if (score >= 90) return 'bg-green-600 text-white';
    if (score >= 80) return 'bg-blue-600 text-white';
    if (score >= 70) return 'bg-yellow-600 text-white';
    return 'bg-gray-600 text-white';
  };

  return (
    <header className="mb-12">
      {/* Title and Category */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Badge variant="outline" className="capitalize">
            {caseStudy.category}
          </Badge>
          {caseStudy.featured && (
            <Badge className="bg-primary text-primary-foreground">
              Featured
            </Badge>
          )}
        </div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          {caseStudy.title}
        </h1>
        <p className="text-xl text-muted-foreground leading-8">
          {caseStudy.summary}
        </p>
      </div>

      {/* Key Metrics */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="flex items-center justify-center mb-2">
                <TrendingUp className="h-4 w-4 text-blue-600 mr-1" />
                <span className="text-2xl font-bold text-blue-600">
                  {caseStudy.impact_score}
                </span>
                <span className="text-sm text-blue-600 ml-1">/100</span>
              </div>
              <p className="text-sm text-muted-foreground">Impact Score</p>
              <Badge
                className={`${getImpactColor(caseStudy.impact_score)} text-xs mt-1`}
              >
                {caseStudy.impact_score >= 90
                  ? 'Excellent'
                  : caseStudy.impact_score >= 80
                    ? 'Very Good'
                    : 'Good'}
              </Badge>
            </div>

            <div>
              <div className="flex items-center justify-center mb-2">
                <DollarSign className="h-4 w-4 text-green-600 mr-1" />
                <span className="text-2xl font-bold text-green-600">
                  {formatCurrency(caseStudy.business_value)}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">Business Value</p>
              <p className="text-xs text-muted-foreground">Quantified impact</p>
            </div>

            <div>
              <div className="flex items-center justify-center mb-2">
                <Clock className="h-4 w-4 text-orange-600 mr-1" />
                <span className="text-2xl font-bold text-orange-600">
                  {caseStudy.duration_hours}h
                </span>
              </div>
              <p className="text-sm text-muted-foreground">Development</p>
              <p className="text-xs text-muted-foreground">
                {caseStudy.readingTime}min read
              </p>
            </div>

            <div>
              <div className="flex items-center justify-center mb-2">
                <Calendar className="h-4 w-4 text-purple-600 mr-1" />
                <span className="text-2xl font-bold text-purple-600">
                  {caseStudy.roi_calculation.toFixed(1)}x
                </span>
              </div>
              <p className="text-sm text-muted-foreground">ROI</p>
              <p className="text-xs text-muted-foreground">
                {new Date(caseStudy.date).toLocaleDateString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Technologies */}
      <div className="mb-6">
        <h3 className="font-semibold mb-3">Technologies Used</h3>
        <div className="flex flex-wrap gap-2">
          {caseStudy.tech.map(tech => (
            <Badge key={tech} variant="secondary">
              {tech}
            </Badge>
          ))}
        </div>

        {caseStudy.architecture && (
          <div className="mt-4">
            <h3 className="font-semibold mb-3">Architecture Patterns</h3>
            <div className="flex flex-wrap gap-2">
              {caseStudy.architecture.map(pattern => (
                <Badge key={pattern} variant="outline">
                  {pattern}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
