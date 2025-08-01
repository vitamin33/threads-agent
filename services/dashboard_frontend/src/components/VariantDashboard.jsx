import React, { useState, useEffect } from 'react';
import { PerformanceSummary } from './PerformanceSummary';
import { OptimizationAlerts } from './OptimizationAlerts';
import { ActiveVariantsTable } from './ActiveVariantsTable';
import { PerformanceChart } from './PerformanceChart';
import { PatternFatigueWarnings } from './PatternFatigueWarnings';
import { EarlyKillFeed } from './EarlyKillFeed';
import { useWebSocket } from '../hooks/useWebSocket';
import { useDashboardData } from '../hooks/useDashboardData';

export function VariantDashboard({ personaId }) {
    const [metrics, setMetrics] = useState(null);
    const { wsConnection, wsStatus } = useWebSocket(personaId, {
        onMessage: (message) => {
            if (message.type === 'initial_data') {
                setMetrics(message.data);
            } else if (message.type === 'variant_update') {
                updateVariantMetrics(message.data);
            }
        }
    });

    const { loading, error, refetch } = useDashboardData(personaId, setMetrics);

    const updateVariantMetrics = (updateData) => {
        setMetrics(prev => {
            if (!prev) return prev;
            
            // Update active variants with new data
            if (updateData.event_type === 'performance_update') {
                const updatedVariants = prev.active_variants.map(variant => 
                    variant.id === updateData.variant_id 
                        ? {
                            ...variant,
                            live_metrics: {
                                ...variant.live_metrics,
                                engagement_rate: updateData.current_er,
                                interactions: updateData.interaction_count
                            }
                        }
                        : variant
                );
                
                return {
                    ...prev,
                    active_variants: updatedVariants
                };
            }
            
            // Add early kill to feed
            if (updateData.event_type === 'early_kill') {
                return {
                    ...prev,
                    early_kills_today: {
                        ...prev.early_kills_today,
                        kills_today: prev.early_kills_today.kills_today + 1
                    },
                    real_time_feed: [updateData, ...prev.real_time_feed].slice(0, 50)
                };
            }
            
            return prev;
        });
    };

    if (loading) {
        return <div className="dashboard-loading">Loading dashboard...</div>;
    }

    if (error) {
        return (
            <div className="dashboard-error">
                <p>Error loading dashboard: {error.message}</p>
                <button onClick={refetch}>Retry</button>
            </div>
        );
    }

    return (
        <div className="variant-dashboard">
            <div className="dashboard-header">
                <h1>Variant Performance Dashboard - {personaId}</h1>
                <div className="connection-status">
                    Status: <span className={`status-${wsStatus}`}>{wsStatus}</span>
                </div>
            </div>
            
            <div className="dashboard-summary-row">
                <PerformanceSummary data={metrics?.summary} />
                <OptimizationAlerts suggestions={metrics?.optimization_opportunities} />
            </div>
            
            <div className="dashboard-main-content">
                <div className="dashboard-left-column">
                    <ActiveVariantsTable variants={metrics?.active_variants} />
                    <PerformanceChart data={metrics?.performance_leaders} />
                </div>
                
                <div className="dashboard-right-column">
                    <PatternFatigueWarnings warnings={metrics?.pattern_fatigue_warnings} />
                    <EarlyKillFeed 
                        kills={metrics?.early_kills_today} 
                        recentEvents={metrics?.real_time_feed}
                    />
                </div>
            </div>
        </div>
    );
}