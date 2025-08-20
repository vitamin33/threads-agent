/**
 * Main Dashboard component for real-time variant performance monitoring.
 * Minimal implementation following TDD principles.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { VariantTable } from './VariantTable';
import { AlertPanel } from './AlertPanel';
import { ThompsonSamplingViz } from './ThompsonSamplingViz';
import { StatisticalSignificanceViz } from './StatisticalSignificanceViz';
import { RevenueAttributionDashboard } from './RevenueAttributionDashboard';

interface Variant {
  variant_id: string;
  engagement_rate: number;
  impressions: number;
  successes: number;
  early_kill_status: string;
  pattern_fatigue_warning: boolean;
  freshness_score: number;
}

interface Alert {
  id: string;
  type: 'early_kill' | 'pattern_fatigue';
  variant_id: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
}

interface WebSocketMessage {
  type: string;
  variant_id?: string;
  new_engagement_rate?: number;
  variants?: Variant[];
}

export const Dashboard: React.FC = () => {
  const [variants, setVariants] = useState<Variant[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [activeView, setActiveView] = useState<'variants' | 'algorithm' | 'statistics' | 'revenue'>('variants');

  // Fetch initial data
  const fetchInitialData = useCallback(async () => {
    try {
      const response = await fetch('/dashboard/variants');
      if (response.ok) {
        const data = await response.json();
        setVariants(data.variants);
        setLoading(false);
      }
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
      setLoading(false);
    }
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      switch (message.type) {
        case 'initial_metrics':
          if (message.variants) {
            setVariants(message.variants);
            setLoading(false);
          }
          break;
          
        case 'metrics_update':
          if (message.variant_id && message.new_engagement_rate !== undefined) {
            setVariants(prev => prev.map(variant => 
              variant.variant_id === message.variant_id
                ? { ...variant, engagement_rate: message.new_engagement_rate! }
                : variant
            ));
          }
          break;
          
        case 'early_kill_alert':
          const earlyKillAlert: Alert = {
            id: `alert_${Date.now()}`,
            type: 'early_kill',
            variant_id: message.variant_id || 'unknown',
            message: `Variant ${message.variant_id} flagged for early termination`,
            severity: 'high',
            timestamp: new Date().toISOString()
          };
          setAlerts(prev => [earlyKillAlert, ...prev]);
          break;
          
        case 'pattern_fatigue_alert':
          const fatigueAlert: Alert = {
            id: `alert_${Date.now()}`,
            type: 'pattern_fatigue',
            variant_id: message.variant_id || 'unknown',
            message: `Pattern fatigue detected for ${message.variant_id}`,
            severity: 'medium',
            timestamp: new Date().toISOString()
          };
          setAlerts(prev => [fatigueAlert, ...prev]);
          break;
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }, []);

  // Set up WebSocket connection
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/dashboard/ws');
    
    ws.addEventListener('open', () => {
      setConnectionStatus('connected');
      console.log('WebSocket connected');
    });
    
    ws.addEventListener('message', handleWebSocketMessage);
    
    ws.addEventListener('close', () => {
      setConnectionStatus('disconnected');
      console.log('WebSocket disconnected');
    });
    
    ws.addEventListener('error', (error) => {
      console.error('WebSocket error:', error);
      setConnectionStatus('disconnected');
    });
    
    setWebsocket(ws);
    
    // Cleanup on unmount
    return () => {
      ws.close();
    };
  }, [handleWebSocketMessage]);

  // Fetch initial data on mount
  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const getConnectionStatusColor = (): string => {
    switch (connectionStatus) {
      case 'connected': return 'green';
      case 'connecting': return 'yellow';
      case 'disconnected': return 'red';
      default: return 'gray';
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <h1>Real-Time Variant Performance Dashboard</h1>
        <div className="loading">Loading variant data...</div>
      </div>
    );
  }

  const renderActiveView = () => {
    switch (activeView) {
      case 'algorithm':
        return <ThompsonSamplingViz />;
      case 'statistics':
        return <StatisticalSignificanceViz />;
      case 'revenue':
        return <RevenueAttributionDashboard />;
      default:
        return (
          <div className="dashboard-content">
            <div className="main-content">
              <VariantTable variants={variants} />
            </div>
            <aside className="sidebar">
              <AlertPanel alerts={alerts} />
            </aside>
          </div>
        );
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🎯 A/B Testing Command Center</h1>
        <div className="header-controls">
          <nav className="view-navigation">
            <button 
              className={`nav-button ${activeView === 'variants' ? 'active' : ''}`}
              onClick={() => setActiveView('variants')}
            >
              📊 Variants
            </button>
            <button 
              className={`nav-button ${activeView === 'algorithm' ? 'active' : ''}`}
              onClick={() => setActiveView('algorithm')}
            >
              🎲 Algorithm
            </button>
            <button 
              className={`nav-button ${activeView === 'statistics' ? 'active' : ''}`}
              onClick={() => setActiveView('statistics')}
            >
              📈 Statistics
            </button>
            <button 
              className={`nav-button ${activeView === 'revenue' ? 'active' : ''}`}
              onClick={() => setActiveView('revenue')}
            >
              💰 Revenue
            </button>
          </nav>
          <div className="connection-status">
            Connection: <span style={{ color: getConnectionStatusColor() }}>
              {connectionStatus}
            </span>
          </div>
        </div>
      </header>
      
      {renderActiveView()}
      
      <style jsx>{`
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          background: white;
          border-bottom: 1px solid #dee2e6;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header-controls {
          display: flex;
          align-items: center;
          gap: 20px;
        }
        
        .view-navigation {
          display: flex;
          gap: 5px;
          background: #f8f9fa;
          padding: 5px;
          border-radius: 8px;
        }
        
        .nav-button {
          padding: 10px 15px;
          border: none;
          background: transparent;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s ease;
        }
        
        .nav-button:hover {
          background: #e9ecef;
        }
        
        .nav-button.active {
          background: #007bff;
          color: white;
        }
        
        .connection-status {
          font-size: 14px;
          font-weight: 500;
        }
      `}</style>
    </div>
  );
};