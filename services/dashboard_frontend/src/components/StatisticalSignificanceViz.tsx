/**
 * Statistical Significance Visualization Component
 * 
 * Shows p-values, confidence intervals, and hypothesis testing results
 * for A/B testing experiments with visual statistical analysis.
 */
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
         ScatterChart, Scatter, ResponsiveContainer, LineChart, Line } from 'recharts';

interface ExperimentStats {
  experiment_id: string;
  experiment_name: string;
  sample_sizes: {
    control: number;
    treatment: number;
    total: number;
  };
  conversion_rates: {
    control: number;
    treatment: number;
    improvement: number;
  };
  statistical_results: {
    is_significant: boolean;
    p_value: number | null;
    statistical_power: number;
  };
  visualization_data: {
    effect_size: number;
    confidence_interval: {
      difference: number;
      lower_bound: number;
      upper_bound: number;
      margin_of_error: number;
    };
  };
}

interface StatisticalData {
  experiments: ExperimentStats[];
  statistical_summary: {
    total_experiments: number;
    significant_results: number;
    significance_rate: number;
    avg_effect_size: number;
    avg_sample_size: number;
  };
  methodology: {
    test_type: string;
    significance_level: number;
    confidence_level: number;
    hypothesis: string;
  };
}

export const StatisticalSignificanceViz: React.FC = () => {
  const [data, setData] = useState<StatisticalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);

  useEffect(() => {
    fetchSignificanceData();
    
    const interval = setInterval(fetchSignificanceData, 15000); // 15 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSignificanceData = async () => {
    try {
      const response = await fetch('/api/statistical-analysis/significance');
      if (response.ok) {
        const sigData = await response.json();
        setData(sigData);
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to fetch statistical significance data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="statistical-viz loading">
        <h2>Statistical Significance Analysis</h2>
        <div className="loading-indicator">Loading statistical data...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="statistical-viz error">
        <h2>Statistical Significance Analysis</h2>
        <div className="error-message">Failed to load statistical data</div>
      </div>
    );
  }

  // Prepare p-value visualization data
  const pValueData = data.experiments
    .filter(exp => exp.statistical_results.p_value !== null)
    .map(exp => ({
      experiment: exp.experiment_id.substring(0, 8),
      p_value: exp.statistical_results.p_value,
      is_significant: exp.statistical_results.is_significant,
      effect_size: exp.visualization_data.effect_size,
      sample_size: exp.sample_sizes.total
    }));

  // Prepare effect size vs sample size scatter plot
  const effectSizeData = data.experiments.map(exp => ({
    sample_size: exp.sample_sizes.total,
    effect_size: exp.visualization_data.effect_size * 100, // Convert to percentage
    is_significant: exp.statistical_results.is_significant,
    experiment_id: exp.experiment_id,
    p_value: exp.statistical_results.p_value
  }));

  return (
    <div className="statistical-viz">
      <header className="viz-header">
        <h2>📊 Statistical Significance Analysis</h2>
        <div className="summary-stats">
          <span className="stat">
            {data.statistical_summary.significant_results}/{data.statistical_summary.total_experiments} Significant
          </span>
          <span className="stat">
            {data.statistical_summary.significance_rate.toFixed(1)}% Success Rate
          </span>
          <span className="stat">
            Avg Effect: {(data.statistical_summary.avg_effect_size * 100).toFixed(1)}%
          </span>
        </div>
      </header>

      <div className="viz-grid">
        {/* P-Value Distribution */}
        <div className="viz-panel p-values">
          <h3>📈 P-Value Distribution</h3>
          <p className="panel-description">
            P-values below 0.05 (red line) indicate statistically significant results.
          </p>
          
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pValueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="experiment" 
                label={{ value: 'Experiment', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'P-Value', angle: -90, position: 'insideLeft' }}
                domain={[0, 0.1]}
              />
              <Tooltip 
                formatter={(value, name) => [
                  `${Number(value).toFixed(4)}`,
                  name === 'p_value' ? 'P-Value' : name
                ]}
              />
              <Bar 
                dataKey="p_value" 
                fill={(entry: any) => entry.is_significant ? '#28a745' : '#dc3545'}
                name="P-Value"
              />
              {/* Significance line at 0.05 */}
              <Line 
                type="monotone" 
                dataKey={() => 0.05}
                stroke="#dc3545"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Significance Threshold (0.05)"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Effect Size vs Sample Size */}
        <div className="viz-panel effect-size">
          <h3>🎯 Effect Size vs Sample Size</h3>
          <p className="panel-description">
            Larger samples can detect smaller effects. Green = significant, Red = not significant.
          </p>
          
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart data={effectSizeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="sample_size" 
                label={{ value: 'Sample Size', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'Effect Size (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                formatter={(value, name) => [
                  name === 'effect_size' ? `${Number(value).toFixed(2)}%` : Number(value),
                  name === 'effect_size' ? 'Effect Size' : 'Sample Size'
                ]}
                labelFormatter={(sample_size) => `Sample Size: ${sample_size}`}
              />
              <Scatter 
                dataKey="effect_size"
                fill={(entry: any) => entry.is_significant ? '#28a745' : '#dc3545'}
                name="Experiments"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence Intervals */}
        <div className="viz-panel confidence-intervals">
          <h3>📏 Confidence Intervals</h3>
          <p className="panel-description">
            95% confidence intervals for difference in conversion rates.
          </p>
          
          <div className="intervals-list">
            {data.experiments.slice(0, 5).map((exp, index) => (
              <div key={index} className="interval-item">
                <div className="experiment-info">
                  <strong>{exp.experiment_name || exp.experiment_id.substring(0, 12)}</strong>
                  <span className={`significance-badge ${exp.statistical_results.is_significant ? 'significant' : 'not-significant'}`}>
                    {exp.statistical_results.is_significant ? '✅ Significant' : '❌ Not Significant'}
                  </span>
                </div>
                
                <div className="rates-comparison">
                  <span>Control: {exp.conversion_rates.control.toFixed(2)}%</span>
                  <span>Treatment: {exp.conversion_rates.treatment.toFixed(2)}%</span>
                  <span className={`improvement ${exp.conversion_rates.improvement > 0 ? 'positive' : 'negative'}`}>
                    {exp.conversion_rates.improvement > 0 ? '+' : ''}{exp.conversion_rates.improvement.toFixed(1)}%
                  </span>
                </div>
                
                <div className="confidence-interval-viz">
                  <div className="interval-bar">
                    <div 
                      className="interval-range"
                      style={{
                        left: `${Math.max(0, (exp.visualization_data.confidence_interval.lower_bound + 0.5) * 100)}%`,
                        width: `${Math.min(100, Math.abs(exp.visualization_data.confidence_interval.upper_bound - exp.visualization_data.confidence_interval.lower_bound) * 100)}%`,
                        backgroundColor: exp.statistical_results.is_significant ? '#28a74540' : '#dc354540'
                      }}
                    />
                    <div 
                      className="point-estimate"
                      style={{
                        left: `${(exp.visualization_data.confidence_interval.difference + 0.5) * 100}%`
                      }}
                    />
                  </div>
                  <div className="interval-labels">
                    <span>{(exp.visualization_data.confidence_interval.lower_bound * 100).toFixed(1)}%</span>
                    <span className="point-est">{(exp.visualization_data.confidence_interval.difference * 100).toFixed(1)}%</span>
                    <span>{(exp.visualization_data.confidence_interval.upper_bound * 100).toFixed(1)}%</span>
                  </div>
                </div>
                
                {exp.statistical_results.p_value && (
                  <div className="p-value">
                    P-value: {exp.statistical_results.p_value.toFixed(4)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Statistical Methodology */}
        <div className="viz-panel methodology">
          <h3>🔬 Statistical Methodology</h3>
          
          <div className="methodology-details">
            <div className="method-item">
              <strong>Test Type:</strong> {data.methodology.test_type}
            </div>
            <div className="method-item">
              <strong>Significance Level:</strong> α = {data.methodology.significance_level}
            </div>
            <div className="method-item">
              <strong>Confidence Level:</strong> {(data.methodology.confidence_level * 100)}%
            </div>
            <div className="method-item">
              <strong>Hypothesis:</strong> {data.methodology.hypothesis}
            </div>
          </div>
          
          <div className="interpretation-guide">
            <h4>Interpretation Guide:</h4>
            <ul>
              <li><strong>P-value &lt; 0.05:</strong> Statistically significant difference</li>
              <li><strong>Confidence Interval:</strong> Range of plausible effect sizes</li>
              <li><strong>Effect Size:</strong> Practical significance magnitude</li>
              <li><strong>Sample Size:</strong> Larger samples detect smaller effects</li>
            </ul>
          </div>
        </div>
      </div>

      <style jsx>{`
        .statistical-viz {
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
        
        .summary-stats {
          display: flex;
          gap: 20px;
        }
        
        .stat {
          padding: 8px 12px;
          background: #e9ecef;
          border-radius: 4px;
          font-weight: 500;
        }
        
        .viz-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
        }
        
        .viz-panel {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .intervals-list {
          max-height: 400px;
          overflow-y: auto;
        }
        
        .interval-item {
          margin-bottom: 20px;
          padding: 15px;
          border: 1px solid #dee2e6;
          border-radius: 8px;
        }
        
        .experiment-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        
        .significance-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
        }
        
        .significance-badge.significant {
          background: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }
        
        .significance-badge.not-significant {
          background: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }
        
        .rates-comparison {
          display: flex;
          gap: 15px;
          margin-bottom: 10px;
          font-size: 14px;
        }
        
        .improvement.positive {
          color: #28a745;
          font-weight: 500;
        }
        
        .improvement.negative {
          color: #dc3545;
          font-weight: 500;
        }
        
        .confidence-interval-viz {
          margin: 10px 0;
        }
        
        .interval-bar {
          position: relative;
          height: 20px;
          background: #e9ecef;
          border-radius: 10px;
          margin-bottom: 5px;
        }
        
        .interval-range {
          position: absolute;
          height: 100%;
          border-radius: 10px;
          border: 2px solid #007bff;
        }
        
        .point-estimate {
          position: absolute;
          width: 3px;
          height: 100%;
          background: #dc3545;
          z-index: 1;
        }
        
        .interval-labels {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
        }
        
        .point-est {
          font-weight: bold;
          color: #dc3545;
        }
        
        .p-value {
          font-size: 12px;
          color: #666;
          text-align: center;
          margin-top: 5px;
        }
        
        .methodology-details {
          margin-bottom: 15px;
        }
        
        .method-item {
          margin-bottom: 8px;
          padding: 8px;
          background: #f8f9fa;
          border-radius: 4px;
        }
        
        .interpretation-guide ul {
          margin: 10px 0;
          padding-left: 20px;
        }
        
        .interpretation-guide li {
          margin-bottom: 5px;
        }
      `}</style>
    </div>
  );
};