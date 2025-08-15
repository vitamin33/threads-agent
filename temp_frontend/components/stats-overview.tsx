import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, DollarSign, Clock, Target, BarChart3 } from 'lucide-react';

interface StatsOverviewProps {
  totalCases: number;
  totalValue: number;
  avgImpact: number;
  totalHours: number;
  avgROI: number;
  categories: {
    infrastructure: number;
    optimization: number;
    feature: number;
  };
}

export function StatsOverview({
  totalCases,
  totalValue,
  avgImpact,
  totalHours,
  avgROI,
  categories,
}: StatsOverviewProps) {
  const formatCurrency = (value: number): string => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  return (
    <section className="mb-16">
      <h2 className="text-2xl font-bold text-center mb-8">
        Portfolio Overview
      </h2>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4 mb-8">
        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              <BarChart3 className="h-4 w-4 text-blue-600 mr-1" />
              <span className="text-2xl font-bold text-blue-600">
                {totalCases}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">Case Studies</p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              <DollarSign className="h-4 w-4 text-green-600 mr-1" />
              <span className="text-2xl font-bold text-green-600">
                {formatCurrency(totalValue)}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">Total Value</p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp className="h-4 w-4 text-purple-600 mr-1" />
              <span className="text-2xl font-bold text-purple-600">
                {avgImpact}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">Avg Impact</p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              <Clock className="h-4 w-4 text-orange-600 mr-1" />
              <span className="text-2xl font-bold text-orange-600">
                {totalHours}h
              </span>
            </div>
            <p className="text-sm text-muted-foreground">Total Work</p>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              <Target className="h-4 w-4 text-red-600 mr-1" />
              <span className="text-2xl font-bold text-red-600">
                {avgROI.toFixed(1)}x
              </span>
            </div>
            <p className="text-sm text-muted-foreground">Avg ROI</p>
          </CardContent>
        </Card>
      </div>

      {/* Category Breakdown */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-center">Case Study Categories</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600 mb-1">
                {categories.infrastructure}
              </div>
              <Badge variant="secondary">Infrastructure</Badge>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 mb-1">
                {categories.optimization}
              </div>
              <Badge variant="secondary">Optimization</Badge>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600 mb-1">
                {categories.feature}
              </div>
              <Badge variant="secondary">Feature</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Data Notice */}
      <div className="text-center">
        <p className="text-sm text-muted-foreground">
          Metrics updated from live production systems and GitHub repositories
        </p>
      </div>
    </section>
  );
}
