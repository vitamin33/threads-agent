/**
 * Thompson Sampling Algorithm Visualization Component
 * 
 * Shows Beta distributions, sampling decisions, and algorithm performance
 * with real-time updates from the dashboard API.
 */
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
         AreaChart, Area, BarChart, Bar, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';

interface BetaDistribution {
  variant_id: string;
  curve_data: {
    x_values: number[];
    y_values: number[];
    peak_x: number;
    peak_y: number;
  };
  statistical_measures: {
    credible_interval_95: {
      lower: number;
      upper: number;
    };
    mean: number;
    uncertainty: number;
  };
  sampling_weight: number;
  variant_info: {
    dimensions: Record<string, string>;
    performance: {
      impressions: number;
      successes: number;
    };
  };
}

interface SamplingDecision {
  round: number;
  selected_variant: string;
  selection_value: number;
  all_samples: Array<{
    variant_id: string;
    sample_value: number;
    alpha: number;
    beta: number;
  }>;
}

interface ThompsonSamplingData {
  algorithm_state: {
    total_variants: number;
    active_sampling: boolean;
    algorithm_type: string;
  };
  beta_distributions: Record<string, BetaDistribution>;
  recent_decisions: SamplingDecision[];
  algorithm_metrics: {
    exploration_exploitation: {
      exploration_percentage: number;
      exploitation_percentage: number;
    };
  };
}

export const ThompsonSamplingViz: React.FC = () => {
  const [data, setData] = useState<ThompsonSamplingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedVariant, setSelectedVariant] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);

  useEffect(() => {
    fetchVisualizationData();
    
    // Set up periodic refresh
    const interval = setInterval(fetchVisualizationData, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchVisualizationData = async () => {
    try {
      const response = await fetch('/api/thompson-sampling/visualization');
      if (response.ok) {
        const vizData = await response.json();
        setData(vizData);
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to fetch Thompson Sampling visualization data:', error);
      setLoading(false);
    }
  };

  const runSamplingDemo = async () => {
    setDemoMode(true);
    try {
      const response = await fetch('/api/thompson-sampling/demo');
      if (response.ok) {
        const demoData = await response.json();
        // Update with demo data
        setData(prev => prev ? { ...prev, recent_decisions: demoData.sampling_demonstration } : null);
      }
    } catch (error) {
      console.error('Failed to run sampling demo:', error);
    }
    setDemoMode(false);
  };

  if (loading) {
    return (
      <div className="thompson-sampling-viz loading">
        <h2>Thompson Sampling Algorithm Visualization</h2>
        <div className="loading-indicator">Loading algorithm data...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="thompson-sampling-viz error">
        <h2>Thompson Sampling Algorithm Visualization</h2>
        <div className="error-message">Failed to load visualization data</div>
      </div>
    );
  }

  // Prepare Beta distribution chart data
  const betaChartData = Object.entries(data.beta_distributions).map(([variantId, dist]) => {
    return dist.curve_data.x_values.map((x, i) => ({
      x: x * 100, // Convert to percentage
      [variantId]: dist.curve_data.y_values[i],
      [`${variantId}_mean`]: x === Math.round(dist.statistical_measures.mean * 100) / 100 ? dist.curve_data.y_values[i] : null
    }));
  }).reduce((acc, curr) => {
    curr.forEach((point, i) => {
      if (!acc[i]) acc[i] = { x: point.x };
      Object.assign(acc[i], point);
    });
    return acc;
  }, [] as any[]);

  // Prepare sampling decisions chart data
  const samplingChartData = data.recent_decisions.map(decision => ({
    round: decision.round,
    selected_variant: decision.selected_variant,
    selection_value: decision.selection_value,
    timestamp: decision.round
  }));

  const variantColors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];

  return (
    <div className="thompson-sampling-viz">
      <header className="viz-header">
        <h2>🎯 Thompson Sampling Algorithm Visualization</h2>
        <div className="algorithm-status">
          <span className="status-indicator active">
            {data.algorithm_state.active_sampling ? '🟢 Active' : '🔴 Inactive'}
          </span>
          <span className="variant-count">
            {data.algorithm_state.total_variants} Variants
          </span>
          <button 
            onClick={runSamplingDemo}
            disabled={demoMode}
            className="demo-button"
          >
            {demoMode ? '⏳ Running Demo...' : '▶️ Run Demo'}
          </button>
        </div>
      </header>

      <div className="viz-grid">
        {/* Beta Distributions Plot */}
        <div className="viz-panel beta-distributions">
          <h3>📊 Beta Distribution Curves</h3>
          <p className="panel-description">
            Each curve shows the uncertainty about a variant's true success rate.
            Taller, narrower curves = more confidence. Wider curves = more uncertainty.
          </p>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={betaChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="x" 
                label={{ value: 'Success Rate (%)', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'Probability Density', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [`${Number(value).toFixed(3)}`, `${name} PDF`]}
                labelFormatter={(x) => `Success Rate: ${x}%`}
              />
              <Legend />
              {Object.keys(data.beta_distributions).map((variantId, index) => (
                <Line
                  key={variantId}
                  type="monotone"
                  dataKey={variantId}
                  stroke={variantColors[index % variantColors.length]}
                  strokeWidth={2}
                  dot={false}
                  name={`${variantId} (α=${data.beta_distributions[variantId].statistical_measures.mean.toFixed(2)})`}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence Intervals */}
        <div className="viz-panel confidence-intervals">
          <h3>📈 95% Confidence Intervals</h3>
          <p className="panel-description">
            Credible intervals show the range where the true success rate likely falls.
          </p>
          
          <div className="confidence-list">
            {Object.entries(data.beta_distributions).map(([variantId, dist]) => (
              <div key={variantId} className="confidence-item">
                <div className="variant-label">
                  <strong>{variantId}</strong>
                  <span className="dimensions">
                    {Object.entries(dist.variant_info.dimensions).map(([k, v]) => `${k}: ${v}`).join(', ')}
                  </span>
                </div>
                <div className="confidence-bar">
                  <div className="bar-container">
                    <div 
                      className="confidence-range"
                      style={{
                        left: `${dist.statistical_measures.credible_interval_95.lower * 100}%`,
                        width: `${(dist.statistical_measures.credible_interval_95.upper - dist.statistical_measures.credible_interval_95.lower) * 100}%`,
                        backgroundColor: variantColors[Object.keys(data.beta_distributions).indexOf(variantId) % variantColors.length] + '40'
                      }}
                    />
                    <div 
                      className="mean-line"
                      style={{
                        left: `${dist.statistical_measures.mean * 100}%`
                      }}
                    />
                  </div>
                  <div className="interval-labels">
                    <span>{(dist.statistical_measures.credible_interval_95.lower * 100).toFixed(1)}%</span>
                    <span className="mean">{(dist.statistical_measures.mean * 100).toFixed(1)}%</span>
                    <span>{(dist.statistical_measures.credible_interval_95.upper * 100).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="uncertainty-score">
                  Uncertainty: {(dist.statistical_measures.uncertainty * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Sampling Decisions */}
        <div className="viz-panel sampling-decisions">
          <h3>🎲 Recent Sampling Decisions</h3>
          <p className="panel-description">
            Live Thompson Sampling selections showing which variants were chosen and why.
          </p>
          
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={samplingChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="round" label={{ value: 'Selection Round', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Sampled Value', angle: -90, position: 'insideLeft' }} />
              <Tooltip 
                formatter={(value, name) => [`${Number(value).toFixed(3)}`, 'Sampled Value']}
                labelFormatter={(round) => `Round ${round}`}
              />
              <Bar dataKey="selection_value" fill="#8884d8" name="Selection Value" />
            </BarChart>
          </ResponsiveContainer>
          
          <div className="decisions-list">
            {data.recent_decisions.slice(0, 5).map((decision, index) => (
              <div key={index} className="decision-item">
                <div className="decision-header">
                  <span className="round">Round {decision.round}</span>
                  <span className="selected-variant">{decision.selected_variant}</span>
                  <span className="selection-value">{decision.selection_value.toFixed(3)}</span>
                </div>
                <div className="all-samples">
                  {decision.all_samples.map((sample, i) => (
                    <span 
                      key={i} 
                      className={`sample ${sample.variant_id === decision.selected_variant ? 'selected' : ''}`}
                    >
                      {sample.variant_id}: {sample.sample_value.toFixed(3)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Algorithm Performance Metrics */}
        <div className="viz-panel algorithm-metrics">
          <h3>⚡ Algorithm Performance</h3>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-value">
                {data.algorithm_metrics.exploration_exploitation?.exploration_percentage?.toFixed(1) || 0}%
              </div>
              <div className="metric-label">Exploration</div>
              <div className="metric-description">Learning new variants</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">
                {data.algorithm_metrics.exploration_exploitation?.exploitation_percentage?.toFixed(1) || 0}%
              </div>
              <div className="metric-label">Exploitation</div>
              <div className="metric-description">Using known winners</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">
                {Object.keys(data.beta_distributions).length}
              </div>
              <div className="metric-label">Active Variants</div>
              <div className="metric-description">Being optimized</div>
            </div>
            
            <div className="metric-card">
              <div className="metric-value">Optimal</div>
              <div className="metric-label">Regret Bound</div>
              <div className="metric-description">O(√n log n)</div>
            </div>
          </div>
        </div>

        {/* Mathematical Foundation */}
        <div className="viz-panel math-foundation">
          <h3>🧮 Mathematical Foundation</h3>
          
          <div className="math-explanation">
            <div className="math-step">
              <strong>1. Prior:</strong> Beta(1, 1) - Uniform prior belief
            </div>
            <div className="math-step">
              <strong>2. Posterior:</strong> Beta(α + successes, β + failures)
            </div>
            <div className="math-step">
              <strong>3. Sampling:</strong> θᵢ ~ Beta(αᵢ, βᵢ) for each variant i
            </div>
            <div className="math-step">
              <strong>4. Selection:</strong> argmax_i(θᵢ) - Choose highest sampled value
            </div>
          </div>
          
          <div className="business-interpretation">
            <h4>Business Interpretation:</h4>
            <ul>
              <li><strong>Exploration:</strong> Try uncertain variants to learn more</li>
              <li><strong>Exploitation:</strong> Use known high-performers more often</li>
              <li><strong>Balance:</strong> Automatically optimizes based on uncertainty</li>
              <li><strong>Outcome:</strong> Maximizes long-term engagement/revenue</li>
            </ul>
          </div>
        </div>
      </div>

      <style jsx>{`
        .thompson-sampling-viz {
          padding: 20px;
          background: #f8f9fa;
          min-height: 100vh;
        }
        
        .viz-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          padding: 20px;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .algorithm-status {
          display: flex;
          gap: 15px;
          align-items: center;
        }
        
        .demo-button {
          padding: 8px 16px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
        }
        
        .demo-button:disabled {
          background: #6c757d;
          cursor: not-allowed;
        }
        
        .viz-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin-bottom: 20px;
        }
        
        .viz-panel {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .viz-panel h3 {
          margin: 0 0 10px 0;
          color: #333;
        }
        
        .panel-description {
          color: #666;
          font-size: 14px;
          margin-bottom: 15px;
        }
        
        .confidence-list {
          space-y: 15px;
        }
        
        .confidence-item {
          margin-bottom: 15px;
        }
        
        .variant-label {
          display: flex;
          justify-content: space-between;
          margin-bottom: 5px;
        }
        
        .dimensions {
          font-size: 12px;
          color: #666;
        }
        
        .bar-container {
          position: relative;
          height: 20px;
          background: #e9ecef;
          border-radius: 10px;
          margin-bottom: 5px;
        }
        
        .confidence-range {
          position: absolute;
          height: 100%;
          border-radius: 10px;
          border: 2px solid #007bff;
        }
        
        .mean-line {
          position: absolute;
          width: 2px;
          height: 100%;
          background: #dc3545;
          z-index: 1;
        }
        
        .interval-labels {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
        }
        
        .mean {
          font-weight: bold;
          color: #dc3545;
        }
        
        .decisions-list {
          max-height: 200px;
          overflow-y: auto;
        }
        
        .decision-item {
          margin-bottom: 10px;
          padding: 10px;
          background: #f8f9fa;
          border-radius: 4px;
        }
        
        .decision-header {
          display: flex;
          justify-content: space-between;
          font-weight: 500;
          margin-bottom: 5px;
        }
        
        .all-samples {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }
        
        .sample {
          padding: 2px 6px;
          background: #e9ecef;
          border-radius: 3px;
          font-size: 12px;
        }
        
        .sample.selected {
          background: #007bff;
          color: white;
        }
        
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 15px;
        }
        
        .metric-card {
          text-align: center;
          padding: 15px;
          background: #f8f9fa;
          border-radius: 8px;
        }
        
        .metric-value {
          font-size: 24px;
          font-weight: bold;
          color: #007bff;
        }
        
        .metric-label {
          font-weight: 500;
          margin: 5px 0;
        }
        
        .metric-description {
          font-size: 12px;
          color: #666;
        }
        
        .math-explanation {
          margin-bottom: 20px;
        }
        
        .math-step {
          margin-bottom: 8px;
          font-family: 'Courier New', monospace;
          background: #f8f9fa;
          padding: 8px;
          border-radius: 4px;
        }
        
        .business-interpretation ul {
          margin: 10px 0;
          padding-left: 20px;
        }
        
        .business-interpretation li {
          margin-bottom: 5px;
        }
        
        .loading, .error {
          text-align: center;
          padding: 50px;
        }
        
        .loading-indicator, .error-message {
          color: #666;
          margin-top: 20px;
        }
      `}</style>
    </div>
  );
};