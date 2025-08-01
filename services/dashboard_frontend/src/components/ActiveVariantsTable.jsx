import React from 'react';
import { formatDistanceToNow } from 'date-fns';

export function ActiveVariantsTable({ variants = [] }) {
    const getPerformanceClass = (actual, predicted) => {
        const ratio = actual / predicted;
        if (ratio >= 0.9) return 'performance-good';
        if (ratio >= 0.7) return 'performance-warning';
        return 'performance-poor';
    };

    const getVariantStatusClass = (variant) => {
        if (variant.status === 'killed') return 'variant-killed';
        const performanceRatio = variant.live_metrics?.engagement_rate / variant.predicted_er;
        if (performanceRatio < 0.5) return 'variant-at-risk';
        return 'variant-active';
    };

    return (
        <div className="variants-table-container">
            <h3>Active Variants (Live Performance)</h3>
            <div className="table-wrapper">
                <table className="variants-table">
                    <thead>
                        <tr>
                            <th>Content Preview</th>
                            <th>Predicted ER</th>
                            <th>Actual ER</th>
                            <th>Delta</th>
                            <th>Interactions</th>
                            <th>Time Active</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {variants.length === 0 ? (
                            <tr>
                                <td colSpan="7" className="no-data">No active variants</td>
                            </tr>
                        ) : (
                            variants.map(variant => (
                                <tr key={variant.id} className={getVariantStatusClass(variant)}>
                                    <td className="content-preview">
                                        <span title={variant.content}>
                                            {variant.content.slice(0, 50)}...
                                        </span>
                                    </td>
                                    <td>{(variant.predicted_er * 100).toFixed(1)}%</td>
                                    <td className={getPerformanceClass(
                                        variant.live_metrics?.engagement_rate || 0, 
                                        variant.predicted_er
                                    )}>
                                        {((variant.live_metrics?.engagement_rate || 0) * 100).toFixed(1)}%
                                    </td>
                                    <td className={variant.performance_vs_prediction >= 0 ? 'delta-positive' : 'delta-negative'}>
                                        {variant.performance_vs_prediction >= 0 ? '+' : ''}
                                        {(variant.performance_vs_prediction * 100).toFixed(1)}%
                                    </td>
                                    <td>{variant.live_metrics?.interactions || 0}</td>
                                    <td>{variant.time_since_post || 'N/A'}</td>
                                    <td>
                                        <StatusBadge status={variant.status} />
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

function StatusBadge({ status }) {
    const statusClass = `status-badge status-${status}`;
    return <span className={statusClass}>{status}</span>;
}