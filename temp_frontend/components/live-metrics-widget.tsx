'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  DollarSign,
  Clock,
  Target,
  ExternalLink,
} from 'lucide-react';

interface Achievement {
  id: string;
  title: string;
  impact_score: number;
  business_value: number;
  performance_improvement: number;
  duration_hours: number;
  link: string;
  evidence: {
    pr_number?: number;
    before_metrics: Record<string, any>;
    after_metrics: Record<string, any>;
  };
}

interface LiveMetricsWidgetProps {
  achievement: Achievement;
}

export function LiveMetricsWidget({ achievement }: LiveMetricsWidgetProps) {
  const formatCurrency = (value: number): string => {
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
    <Card className="border-2 border-primary/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            Live Achievement Metrics
          </CardTitle>
          <Badge
            className={`${getImpactColor(achievement.impact_score)} text-white`}
          >
            Impact: {achievement.impact_score}/100
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 rounded-lg bg-green-50">
            <div className="flex items-center justify-center mb-1">
              <DollarSign className="h-4 w-4 text-green-600 mr-1" />
              <span className="text-xl font-bold text-green-600">
                {formatCurrency(achievement.business_value)}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">Business Value</p>
          </div>

          <div className="text-center p-3 rounded-lg bg-blue-50">
            <div className="flex items-center justify-center mb-1">
              <TrendingUp className="h-4 w-4 text-blue-600 mr-1" />
              <span className="text-xl font-bold text-blue-600">
                +{achievement.performance_improvement.toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-muted-foreground">Performance</p>
          </div>

          <div className="text-center p-3 rounded-lg bg-orange-50">
            <div className="flex items-center justify-center mb-1">
              <Clock className="h-4 w-4 text-orange-600 mr-1" />
              <span className="text-xl font-bold text-orange-600">
                {achievement.duration_hours}h
              </span>
            </div>
            <p className="text-xs text-muted-foreground">Duration</p>
          </div>

          <div className="text-center p-3 rounded-lg bg-purple-50">
            <div className="flex items-center justify-center mb-1">
              <Target className="h-4 w-4 text-purple-600 mr-1" />
              <span className="text-xl font-bold text-purple-600">
                {(
                  achievement.business_value /
                  (achievement.duration_hours * 150)
                ).toFixed(1)}
                x
              </span>
            </div>
            <p className="text-xs text-muted-foreground">ROI</p>
          </div>
        </div>

        {/* Evidence Link */}
        <div className="flex items-center justify-between pt-4 border-t">
          <span className="text-sm text-muted-foreground">
            Linked Achievement: {achievement.title}
          </span>
          <a
            href={achievement.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
            {achievement.evidence.pr_number &&
              `PR #${achievement.evidence.pr_number}`}
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
