/**
 * AlertPanel component for displaying performance alerts.
 * Minimal implementation following TDD principles.
 */
import React from 'react';

interface Alert {
  id: string;
  type: 'early_kill' | 'pattern_fatigue';
  variant_id: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  timestamp: string;
}

interface AlertPanelProps {
  alerts: Alert[];
}

export const AlertPanel: React.FC<AlertPanelProps> = ({ alerts }) => {
  // Sort alerts by timestamp (newest first)
  const sortedAlerts = [...alerts].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const getAlertTypeLabel = (type: string): string => {
    switch (type) {
      case 'early_kill':
        return 'Early Kill';
      case 'pattern_fatigue':
        return 'Pattern Fatigue';
      default:
        return 'Alert';
    }
  };

  return (
    <div className="alert-panel">
      <h3>Performance Alerts</h3>
      
      {sortedAlerts.length === 0 ? (
        <div className="no-alerts">No active alerts</div>
      ) : (
        <div className="alerts-list">
          {sortedAlerts.map((alert) => (
            <div key={alert.id} className={`alert severity-${alert.severity}`}>
              <div className="alert-header">
                <span className="alert-type">{getAlertTypeLabel(alert.type)}</span>
                <span className="alert-timestamp">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <div className="alert-message">{alert.message}</div>
              <div className="alert-variant">Variant: {alert.variant_id}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};