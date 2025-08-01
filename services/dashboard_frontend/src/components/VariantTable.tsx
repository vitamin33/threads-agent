/**
 * VariantTable component for displaying variant performance data.
 * Minimal implementation following TDD principles.
 */
import React from 'react';

interface Variant {
  variant_id: string;
  engagement_rate: number;
  impressions: number;
  successes: number;
  early_kill_status: string;
  pattern_fatigue_warning: boolean;
  freshness_score: number;
}

interface VariantTableProps {
  variants: Variant[];
}

export const VariantTable: React.FC<VariantTableProps> = ({ variants }) => {
  const getRowClassName = (variant: Variant): string => {
    const classes = [];
    
    // Add warning class for low engagement variants being monitored
    if (variant.early_kill_status === 'monitoring' && variant.engagement_rate < 0.10) {
      classes.push('warning');
    }
    
    // Add pattern fatigue class
    if (variant.pattern_fatigue_warning) {
      classes.push('pattern-fatigue');
    }
    
    return classes.join(' ');
  };

  const formatPercentage = (rate: number): string => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  return (
    <div className="variant-table">
      <table>
        <thead>
          <tr>
            <th>Variant ID</th>
            <th>Engagement Rate</th>
            <th>Impressions</th>
            <th>Successes</th>
            <th>Early Kill Status</th>
            <th>Pattern Fatigue</th>
            <th>Freshness Score</th>
          </tr>
        </thead>
        <tbody>
          {variants.map((variant) => (
            <tr key={variant.variant_id} className={getRowClassName(variant)}>
              <td>{variant.variant_id}</td>
              <td>{formatPercentage(variant.engagement_rate)}</td>
              <td>{variant.impressions}</td>
              <td>{variant.successes}</td>
              <td>{variant.early_kill_status}</td>
              <td>{variant.pattern_fatigue_warning ? 'Yes' : 'No'}</td>
              <td>{variant.freshness_score.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};