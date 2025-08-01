/**
 * Main Dashboard component for real-time variant performance monitoring.
 * Minimal implementation following TDD principles.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { VariantTable } from './VariantTable';
import { AlertPanel } from './AlertPanel';

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

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Real-Time Variant Performance Dashboard</h1>
        <div className="connection-status">
          Connection: <span style={{ color: getConnectionStatusColor() }}>
            {connectionStatus}
          </span>
        </div>
      </header>
      
      <div className="dashboard-content">
        <div className="main-content">
          <VariantTable variants={variants} />
        </div>
        
        <aside className="sidebar">
          <AlertPanel alerts={alerts} />
        </aside>
      </div>
    </div>
  );
};