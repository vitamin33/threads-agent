/**
 * Revenue Attribution Dashboard Component
 * 
 * Shows how A/B testing optimizations impact revenue, MRR, and business KPIs
 * with real-time tracking toward $20k MRR goal.
 */
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
         AreaChart, Area, BarChart, Bar, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface RevenueData {
  current_performance: {
    mrr: number;
    monthly_revenue: number;
    active_subscriptions: number;
    conversion_rate: number;
  };
  ab_testing_impact: {
    best_engagement_rate: number;
    engagement_improvement: number;
    estimated_revenue_increase: number;
    cost_per_follow: number;
    efficiency_gain: number;
  };
  progress_toward_goals: {
    mrr_progress: {
      current: number;
      target: number;
      progress_percentage: number;
      monthly_growth_needed: number;
      on_track: boolean;
    };
  };
  revenue_projections: {
    projections: Array<{
      month: number;
      projected_mrr: number;
      cumulative_growth: number;
      ab_testing_contribution: number;
    }>;
    summary: {
      projected_year_end_mrr: number;
      months_to_target: number | null;
      total_ab_contribution: number;
    };
  };
}

interface ROIData {
  investment_analysis: {
    initial_development_cost: number;
    monthly_operational_cost: number;
    total_investment_3_months: number;
  };
  revenue_attribution: {
    ab_test_conversions: number;
    total_ab_revenue_90_days: number;
    monthly_ab_revenue: number;
  };
  roi_metrics: {
    roi_percentage_90_days: number;
    annual_projected_roi: number;
    payback_period_months: number;
    break_even_status: string;
  };
}

export const RevenueAttributionDashboard: React.FC = () => {
  const [revenueData, setRevenueData] = useState<RevenueData | null>(null);
  const [roiData, setROIData] = useState<ROIData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeframe, setTimeframe] = useState<'3m' | '6m' | '12m'>('12m');

  useEffect(() => {
    fetchRevenueData();
    fetchROIData();
    
    const interval = setInterval(() => {
      fetchRevenueData();
      fetchROIData();
    }, 30000); // 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchRevenueData = async () => {
    try {
      const response = await fetch('/revenue/dashboard');
      if (response.ok) {
        const data = await response.json();
        setRevenueData(data);
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to fetch revenue data:', error);
      setLoading(false);
    }
  };

  const fetchROIData = async () => {
    try {
      const response = await fetch('/revenue/ab-testing-roi');
      if (response.ok) {
        const data = await response.json();
        setROIData(data);
      }
    } catch (error) {
      console.error('Failed to fetch ROI data:', error);
    }
  };

  if (loading) {
    return (
      <div className="revenue-dashboard loading">
        <h2>Revenue Attribution Dashboard</h2>
        <div className="loading-indicator">Loading revenue data...</div>
      </div>
    );
  }

  if (!revenueData) {
    return (
      <div className="revenue-dashboard error">
        <h2>Revenue Attribution Dashboard</h2>
        <div className="error-message">Failed to load revenue data</div>
      </div>
    );
  }

  // Prepare MRR projection chart data
  const projectionData = revenueData.revenue_projections.projections.map(proj => ({
    month: `Month ${proj.month}`,
    projected_mrr: proj.projected_mrr,
    ab_contribution: proj.ab_testing_contribution,
    cumulative_growth: proj.cumulative_growth
  }));

  // Progress toward $20k MRR
  const mrrProgress = revenueData.progress_toward_goals.mrr_progress;
  const progressPercentage = Math.min(100, mrrProgress.progress_percentage);

  // ROI breakdown data for pie chart
  const roiBreakdownData = roiData ? [
    { name: 'Development ROI', value: roiData.roi_metrics.annual_projected_roi, fill: '#8884d8' },
    { name: 'Operational Efficiency', value: 30, fill: '#82ca9d' },
    { name: 'Time Savings', value: 25, fill: '#ffc658' },
    { name: 'Quality Improvements', value: 15, fill: '#ff7c7c' }
  ] : [];

  return (
    <div className="revenue-dashboard">
      <header className="dashboard-header">
        <h2>💰 Revenue Attribution Dashboard</h2>
        <div className="key-metrics">
          <div className="metric-card mrr">
            <div className="metric-value">${mrrProgress.current.toLocaleString()}</div>
            <div className="metric-label">Current MRR</div>
            <div className="metric-target">Target: ${mrrProgress.target.toLocaleString()}</div>
          </div>
          <div className="metric-card engagement">
            <div className="metric-value">{revenueData.ab_testing_impact.best_engagement_rate.toFixed(1)}%</div>
            <div className="metric-label">Best Engagement</div>
            <div className="metric-improvement">+{revenueData.ab_testing_impact.engagement_improvement.toFixed(1)}% from A/B testing</div>
          </div>
          <div className="metric-card roi">
            <div className="metric-value">{roiData?.roi_metrics.annual_projected_roi.toFixed(0) || 0}%</div>
            <div className="metric-label">Annual ROI</div>
            <div className="metric-status">{roiData?.roi_metrics.break_even_status || 'calculating'}</div>
          </div>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* MRR Progress and Projections */}
        <div className="dashboard-panel mrr-projections">
          <h3>📈 MRR Progress & Projections</h3>
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <div className="progress-labels">
              <span>$0</span>
              <span className="current">${mrrProgress.current.toLocaleString()}</span>
              <span className="target">${mrrProgress.target.toLocaleString()}</span>
            </div>
          </div>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={projectionData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis 
                label={{ value: 'MRR ($)', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip 
                formatter={(value, name) => [
                  `$${Number(value).toLocaleString()}`,
                  name === 'projected_mrr' ? 'Projected MRR' : 'A/B Testing Contribution'
                ]}
              />
              <Legend />
              <Line type="monotone" dataKey="projected_mrr" stroke="#8884d8" strokeWidth={3} name="Projected MRR" />
              <Line type="monotone" dataKey="ab_contribution" stroke="#82ca9d" strokeWidth={2} name="A/B Testing Impact" />
            </LineChart>
          </ResponsiveContainer>
          
          <div className="projection-summary">
            <div className="summary-item">
              <strong>Year-end Projection:</strong> ${revenueData.revenue_projections.summary.projected_year_end_mrr.toLocaleString()}
            </div>
            <div className="summary-item">
              <strong>Months to $20k:</strong> {revenueData.revenue_projections.summary.months_to_target || 'Calculating...'}
            </div>
            <div className="summary-item">
              <strong>A/B Testing Value:</strong> ${revenueData.revenue_projections.summary.total_ab_contribution.toLocaleString()}/year
            </div>
          </div>
        </div>

        {/* A/B Testing Revenue Impact */}
        <div className="dashboard-panel ab-impact">
          <h3>🧪 A/B Testing Revenue Impact</h3>
          
          <div className="impact-metrics">
            <div className="impact-card">
              <div className="impact-value">+{revenueData.ab_testing_impact.engagement_improvement.toFixed(1)}%</div>
              <div className="impact-label">Engagement Improvement</div>
              <div className="impact-attribution">From Thompson Sampling</div>
            </div>
            
            <div className="impact-card">
              <div className="impact-value">${revenueData.ab_testing_impact.estimated_revenue_increase.toLocaleString()}</div>
              <div className="impact-label">Monthly Revenue Increase</div>
              <div className="impact-attribution">Attributed to optimization</div>
            </div>
            
            <div className="impact-card">
              <div className="impact-value">${revenueData.ab_testing_impact.cost_per_follow.toFixed(3)}</div>
              <div className="impact-label">Cost per Follow</div>
              <div className="impact-attribution">Efficiency improvement</div>
            </div>
          </div>
          
          <div className="algorithm-contribution">
            <h4>Algorithm Contribution Breakdown:</h4>
            <div className="contribution-list">
              <div className="contribution-item">
                <span className="contribution-label">Thompson Sampling Optimization:</span>
                <span className="contribution-value">+{revenueData.ab_testing_impact.engagement_improvement.toFixed(1)}% engagement</span>
              </div>
              <div className="contribution-item">
                <span className="contribution-label">Cost Efficiency Gains:</span>
                <span className="contribution-value">${(revenueData.ab_testing_impact.efficiency_gain * 1000).toFixed(0)}/month saved</span>
              </div>
              <div className="contribution-item">
                <span className="contribution-label">Revenue Attribution:</span>
                <span className="contribution-value">${revenueData.ab_testing_impact.estimated_revenue_increase.toLocaleString()}/month</span>
              </div>
            </div>
          </div>
        </div>

        {/* ROI Analysis */}
        {roiData && (
          <div className="dashboard-panel roi-analysis">
            <h3>💹 A/B Testing ROI Analysis</h3>
            
            <div className="roi-summary">
              <div className="roi-metric">
                <div className="roi-value">{roiData.roi_metrics.annual_projected_roi.toFixed(0)}%</div>
                <div className="roi-label">Annual ROI</div>
              </div>
              <div className="roi-metric">
                <div className="roi-value">{roiData.roi_metrics.payback_period_months.toFixed(1)}</div>
                <div className="roi-label">Payback (Months)</div>
              </div>
              <div className="roi-metric">
                <div className="roi-value">${roiData.revenue_attribution.monthly_ab_revenue.toLocaleString()}</div>
                <div className="roi-label">Monthly Revenue</div>
              </div>
            </div>
            
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={roiBreakdownData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {roiBreakdownData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>
            
            <div className="investment-breakdown">
              <div className="investment-item">
                <span>Initial Investment:</span>
                <span>${roiData.investment_analysis.initial_development_cost.toLocaleString()}</span>
              </div>
              <div className="investment-item">
                <span>Monthly Operational:</span>
                <span>${roiData.investment_analysis.monthly_operational_cost.toLocaleString()}</span>
              </div>
              <div className="investment-item">
                <span>Revenue Generated:</span>
                <span>${roiData.revenue_attribution.total_ab_revenue_90_days.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* Business KPI Tracking */}
        <div className="dashboard-panel business-kpis">
          <h3>🎯 Business KPI Tracking</h3>
          
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-title">Engagement Rate</span>
                <span className={`kpi-status ${revenueData.ab_testing_impact.best_engagement_rate >= 6.0 ? 'target-met' : 'improving'}`}>
                  {revenueData.ab_testing_impact.best_engagement_rate >= 6.0 ? '✅ Target Met' : '🎯 Improving'}
                </span>
              </div>
              <div className="kpi-value">{revenueData.ab_testing_impact.best_engagement_rate.toFixed(2)}%</div>
              <div className="kpi-target">Target: 6.0%</div>
              <div className="kpi-progress">
                <div 
                  className="kpi-progress-bar"
                  style={{ width: `${Math.min(100, (revenueData.ab_testing_impact.best_engagement_rate / 6.0) * 100)}%` }}
                />
              </div>
            </div>
            
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-title">Cost per Follow</span>
                <span className={`kpi-status ${revenueData.ab_testing_impact.cost_per_follow <= 0.01 ? 'target-met' : 'improving'}`}>
                  {revenueData.ab_testing_impact.cost_per_follow <= 0.01 ? '✅ Target Met' : '🎯 Improving'}
                </span>
              </div>
              <div className="kpi-value">${revenueData.ab_testing_impact.cost_per_follow.toFixed(3)}</div>
              <div className="kpi-target">Target: $0.01</div>
              <div className="kpi-progress">
                <div 
                  className="kpi-progress-bar"
                  style={{ width: `${Math.min(100, (0.01 / Math.max(revenueData.ab_testing_impact.cost_per_follow, 0.001)) * 100)}%` }}
                />
              </div>
            </div>
            
            <div className="kpi-card">
              <div className="kpi-header">
                <span className="kpi-title">Monthly MRR</span>
                <span className={`kpi-status ${mrrProgress.on_track ? 'on-track' : 'needs-acceleration'}`}>
                  {mrrProgress.on_track ? '✅ On Track' : '⚡ Needs Acceleration'}
                </span>
              </div>
              <div className="kpi-value">${mrrProgress.current.toLocaleString()}</div>
              <div className="kpi-target">Target: $20,000</div>
              <div className="kpi-progress">
                <div 
                  className="kpi-progress-bar"
                  style={{ width: `${progressPercentage}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="attribution-insights">
        <h3>🔍 Attribution Insights</h3>
        <div className="insights-list">
          <div className="insight-item">
            <span className="insight-icon">📊</span>
            <div className="insight-content">
              <strong>Thompson Sampling Impact:</strong> 
              {revenueData.ab_testing_impact.engagement_improvement > 2 
                ? ` Significant ${revenueData.ab_testing_impact.engagement_improvement.toFixed(1)}% engagement improvement driving revenue growth`
                : ` Moderate improvement in progress, showing ${revenueData.ab_testing_impact.engagement_improvement.toFixed(1)}% gains`
              }
            </div>
          </div>
          
          <div className="insight-item">
            <span className="insight-icon">💡</span>
            <div className="insight-content">
              <strong>Optimization Opportunity:</strong>
              {mrrProgress.monthly_growth_needed > 5000 
                ? ` Need $${mrrProgress.monthly_growth_needed.toLocaleString()} monthly growth to reach target`
                : ` Close to target! Only $${mrrProgress.monthly_growth_needed.toLocaleString()} growth needed`
              }
            </div>
          </div>
          
          <div className="insight-item">
            <span className="insight-icon">⚡</span>
            <div className="insight-content">
              <strong>Efficiency Gains:</strong>
              Cost per follow improved by ${(revenueData.ab_testing_impact.efficiency_gain * 1000).toFixed(0)} through algorithmic optimization
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .revenue-dashboard {
          padding: 20px;
          background: #f8f9fa;
          min-height: 100vh;
        }
        
        .dashboard-header {
          margin-bottom: 30px;
          padding: 20px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .key-metrics {
          display: flex;
          gap: 20px;
          margin-top: 20px;
        }
        
        .metric-card {
          flex: 1;
          padding: 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 8px;
          text-align: center;
        }
        
        .metric-card.mrr {
          background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        
        .metric-card.engagement {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .metric-card.roi {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .metric-value {
          font-size: 32px;
          font-weight: bold;
          margin-bottom: 5px;
        }
        
        .metric-label {
          font-size: 14px;
          opacity: 0.9;
          margin-bottom: 5px;
        }
        
        .metric-target, .metric-improvement, .metric-status {
          font-size: 12px;
          opacity: 0.8;
        }
        
        .dashboard-grid {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 20px;
          margin-bottom: 20px;
        }
        
        .dashboard-panel {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .progress-bar-container {
          margin: 20px 0;
        }
        
        .progress-bar {
          height: 12px;
          background: #e9ecef;
          border-radius: 6px;
          overflow: hidden;
          margin-bottom: 8px;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
          transition: width 0.5s ease;
        }
        
        .progress-labels {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #666;
        }
        
        .current {
          font-weight: bold;
          color: #28a745;
        }
        
        .target {
          font-weight: bold;
          color: #007bff;
        }
        
        .projection-summary {
          margin-top: 15px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 4px;
        }
        
        .summary-item {
          margin-bottom: 5px;
        }
        
        .impact-metrics {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }
        
        .impact-card {
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
          text-align: center;
          border-left: 4px solid #007bff;
        }
        
        .impact-value {
          font-size: 24px;
          font-weight: bold;
          color: #007bff;
          margin-bottom: 5px;
        }
        
        .impact-label {
          font-weight: 500;
          margin-bottom: 3px;
        }
        
        .impact-attribution {
          font-size: 12px;
          color: #666;
        }
        
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }
        
        .kpi-card {
          padding: 15px;
          border: 1px solid #dee2e6;
          border-radius: 8px;
        }
        
        .kpi-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        
        .kpi-status.target-met {
          color: #28a745;
          font-size: 12px;
        }
        
        .kpi-status.improving, .kpi-status.on-track {
          color: #ffc107;
          font-size: 12px;
        }
        
        .kpi-status.needs-acceleration {
          color: #dc3545;
          font-size: 12px;
        }
        
        .kpi-value {
          font-size: 28px;
          font-weight: bold;
          color: #333;
          margin-bottom: 5px;
        }
        
        .kpi-target {
          font-size: 12px;
          color: #666;
          margin-bottom: 10px;
        }
        
        .kpi-progress {
          height: 8px;
          background: #e9ecef;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .kpi-progress-bar {
          height: 100%;
          background: linear-gradient(90deg, #007bff 0%, #28a745 100%);
          transition: width 0.5s ease;
        }
        
        .attribution-insights {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .insights-list {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        
        .insight-item {
          display: flex;
          align-items: flex-start;
          gap: 10px;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        
        .insight-icon {
          font-size: 20px;
        }
        
        .insight-content {
          flex: 1;
          line-height: 1.4;
        }
      `}</style>
    </div>
  );
};