/**
 * Tests for AlertPanel component.
 * Following TDD - write failing tests first.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AlertPanel } from '../AlertPanel';

describe('AlertPanel', () => {
  test('renders alert panel with title', () => {
    const mockAlerts = [];
    
    render(<AlertPanel alerts={mockAlerts} />);
    
    expect(screen.getByText('Performance Alerts')).toBeInTheDocument();
  });

  test('shows no alerts message when empty', () => {
    const mockAlerts = [];
    
    render(<AlertPanel alerts={mockAlerts} />);
    
    expect(screen.getByText('No active alerts')).toBeInTheDocument();
  });

  test('displays early kill alerts', () => {
    const mockAlerts = [
      {
        id: 'alert_1',
        type: 'early_kill',
        variant_id: 'poor_variant',
        message: 'Variant poor_variant flagged for early termination',
        severity: 'high',
        timestamp: new Date().toISOString()
      }
    ];
    
    render(<AlertPanel alerts={mockAlerts} />);
    
    expect(screen.getByText('Variant poor_variant flagged for early termination')).toBeInTheDocument();
    expect(screen.getByText('Early Kill')).toBeInTheDocument();
  });

  test('displays pattern fatigue alerts', () => {
    const mockAlerts = [
      {
        id: 'alert_2',
        type: 'pattern_fatigue',
        variant_id: 'overused_variant',
        message: 'Pattern fatigue detected for overused_variant',
        severity: 'medium',
        timestamp: new Date().toISOString()
      }
    ];
    
    render(<AlertPanel alerts={mockAlerts} />);
    
    expect(screen.getByText('Pattern fatigue detected for overused_variant')).toBeInTheDocument();
    expect(screen.getByText('Pattern Fatigue')).toBeInTheDocument();
  });

  test('applies correct severity styling', () => {
    const mockAlerts = [
      {
        id: 'high_alert',
        type: 'early_kill',
        variant_id: 'urgent_variant',
        message: 'Urgent: Stop this variant now!',
        severity: 'high',
        timestamp: new Date().toISOString()
      }
    ];
    
    render(<AlertPanel alerts={mockAlerts} />);
    
    const alertElement = screen.getByText('Urgent: Stop this variant now!').closest('.alert');
    expect(alertElement).toHaveClass('severity-high');
  });

  test('sorts alerts by timestamp (newest first)', () => {
    const oldAlert = {
      id: 'old_alert',
      type: 'pattern_fatigue',
      variant_id: 'old_variant',
      message: 'Old alert',
      severity: 'low',
      timestamp: '2024-01-01T00:00:00Z'
    };
    
    const newAlert = {
      id: 'new_alert',
      type: 'early_kill',
      variant_id: 'new_variant',
      message: 'New alert',
      severity: 'high',
      timestamp: '2024-01-02T00:00:00Z'
    };
    
    render(<AlertPanel alerts={[oldAlert, newAlert]} />);
    
    const alerts = screen.getAllByText(/alert/);
    expect(alerts[0]).toHaveTextContent('New alert');
    expect(alerts[1]).toHaveTextContent('Old alert');
  });
});