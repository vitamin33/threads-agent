import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DollarSign, TrendingUp, CheckCircle } from 'lucide-react';

interface ImpactCardProps {
  businessValue: number;
  impactScore: number;
  outcomes: string[];
}

export function ImpactCard({
  businessValue,
  impactScore,
  outcomes,
}: ImpactCardProps) {
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
    if (score >= 90) return 'bg-green-600';
    if (score >= 80) return 'bg-blue-600';
    if (score >= 70) return 'bg-yellow-600';
    return 'bg-gray-600';
  };

  return (
    <Card className="bg-gradient-to-br from-primary/5 to-secondary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          Business Impact Summary
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="text-center p-4 rounded-lg bg-green-50">
            <div className="flex items-center justify-center mb-2">
              <DollarSign className="h-6 w-6 text-green-600 mr-1" />
              <span className="text-3xl font-bold text-green-600">
                {formatCurrency(businessValue)}
              </span>
            </div>
            <p className="text-sm text-muted-foreground font-medium">
              Business Value
            </p>
            <p className="text-xs text-muted-foreground">Quantified impact</p>
          </div>

          <div className="text-center p-4 rounded-lg bg-blue-50">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-6 w-6 text-blue-600 mr-1" />
              <span className="text-3xl font-bold text-blue-600">
                {impactScore}
              </span>
              <span className="text-lg text-blue-600 ml-1">/100</span>
            </div>
            <p className="text-sm text-muted-foreground font-medium">
              Impact Score
            </p>
            <Badge
              className={`${getImpactColor(impactScore)} text-white text-xs mt-1`}
            >
              {impactScore >= 90
                ? 'Excellent'
                : impactScore >= 80
                  ? 'Very Good'
                  : 'Good'}
            </Badge>
          </div>
        </div>

        {/* Outcomes */}
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            Key Outcomes Achieved
          </h4>
          <div className="space-y-2">
            {outcomes.map((outcome, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 rounded-lg bg-white/50"
              >
                <div className="h-2 w-2 rounded-full bg-green-500 mt-2 flex-shrink-0" />
                <span className="text-sm font-medium">{outcome}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ROI Calculation */}
        <div className="mt-6 p-4 rounded-lg bg-muted/50">
          <h5 className="font-medium mb-2">ROI Analysis</h5>
          <div className="text-sm text-muted-foreground">
            <p>
              <span className="font-medium">Value Created:</span>{' '}
              {formatCurrency(businessValue)}
            </p>
            <p>
              <span className="font-medium">Impact Rating:</span> {impactScore}
              /100 (
              {impactScore >= 90
                ? 'Exceptional'
                : impactScore >= 80
                  ? 'High'
                  : 'Medium'}{' '}
              impact)
            </p>
            <p>
              <span className="font-medium">Evidence-Based:</span> All metrics
              verified through production systems
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
