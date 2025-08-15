import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, ArrowRight } from 'lucide-react';

interface MetricsComparisonProps {
  beforeMetrics: Record<string, any>;
  afterMetrics: Record<string, any>;
}

export function MetricsComparison({
  beforeMetrics,
  afterMetrics,
}: MetricsComparisonProps) {
  const calculateImprovement = (
    before: string | number,
    after: string | number
  ): number | null => {
    // Convert to numbers if they're strings with units
    const parseMetric = (value: string | number): number | null => {
      if (typeof value === 'number') return value;

      const str = value.toString().toLowerCase();

      // Handle percentage values
      if (str.includes('%')) {
        return parseFloat(str.replace('%', ''));
      }

      // Handle time values
      if (str.includes('min')) {
        return parseFloat(str.replace('min', ''));
      }

      if (str.includes('sec') || str.includes('s')) {
        const num = parseFloat(str.replace(/sec|s/g, ''));
        return str.includes('min') ? num : num; // Convert to consistent unit
      }

      // Handle currency values
      if (str.includes('$')) {
        return parseFloat(str.replace(/[$,]/g, ''));
      }

      // Try to parse as number
      const num = parseFloat(str);
      return isNaN(num) ? null : num;
    };

    const beforeNum = parseMetric(before);
    const afterNum = parseMetric(after);

    if (beforeNum === null || afterNum === null) return null;

    return ((afterNum - beforeNum) / beforeNum) * 100;
  };

  const formatMetricValue = (value: any): string => {
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    return String(value);
  };

  const getTrendIcon = (improvement: number | null, metricKey: string) => {
    if (improvement === null) return null;

    // For cost and time metrics, lower is better
    const lowerIsBetter =
      metricKey.includes('cost') ||
      metricKey.includes('time') ||
      metricKey.includes('latency');

    if (lowerIsBetter) {
      return improvement < 0 ? (
        <TrendingUp className="h-3 w-3 text-green-600" />
      ) : (
        <TrendingDown className="h-3 w-3 text-red-600" />
      );
    } else {
      return improvement > 0 ? (
        <TrendingUp className="h-3 w-3 text-green-600" />
      ) : (
        <TrendingDown className="h-3 w-3 text-red-600" />
      );
    }
  };

  const getImprovementText = (
    improvement: number | null,
    metricKey: string
  ): string => {
    if (improvement === null) return '';

    const lowerIsBetter =
      metricKey.includes('cost') ||
      metricKey.includes('time') ||
      metricKey.includes('latency');
    const absImprovement = Math.abs(improvement);

    if (lowerIsBetter) {
      return improvement < 0
        ? `↓${absImprovement.toFixed(1)}%`
        : `↑${absImprovement.toFixed(1)}%`;
    } else {
      return improvement > 0
        ? `↑${improvement.toFixed(1)}%`
        : `↓${absImprovement.toFixed(1)}%`;
    }
  };

  return (
    <Card className="mb-8">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowRight className="h-5 w-5 text-primary" />
          Before vs After Metrics
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          {Object.keys(beforeMetrics).map(key => {
            const beforeValue = beforeMetrics[key];
            const afterValue = afterMetrics[key];
            const improvement = calculateImprovement(beforeValue, afterValue);
            const trendIcon = getTrendIcon(improvement, key);
            const improvementText = getImprovementText(improvement, key);

            return (
              <div
                key={key}
                className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg bg-muted/30"
              >
                <div className="md:col-span-1">
                  <h4 className="font-medium capitalize mb-1">
                    {key.replace(/_/g, ' ')}
                  </h4>
                  {improvement !== null && (
                    <div className="flex items-center gap-1 text-sm">
                      {trendIcon}
                      <span className="font-medium">{improvementText}</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between md:col-span-2">
                  {/* Before */}
                  <div className="text-center">
                    <div className="text-sm text-muted-foreground mb-1">
                      Before
                    </div>
                    <div className="text-lg font-semibold">
                      {formatMetricValue(beforeValue)}
                    </div>
                  </div>

                  {/* Arrow */}
                  <ArrowRight className="h-4 w-4 text-muted-foreground mx-4" />

                  {/* After */}
                  <div className="text-center">
                    <div className="text-sm text-muted-foreground mb-1">
                      After
                    </div>
                    <div className="text-lg font-semibold text-green-600">
                      {formatMetricValue(afterValue)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
