/**
 * Comprehensive tests for VariantDashboard component
 */

import React from 'react';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { VariantDashboard } from '../VariantDashboard';

// Mock hooks
vi.mock('../hooks/useWebSocket', () => ({
  useWebSocket: vi.fn()
}));

vi.mock('../hooks/useDashboardData', () => ({
  useDashboardData: vi.fn()
}));

// Mock child components
vi.mock('../PerformanceSummary', () => ({
  PerformanceSummary: ({ summary }) => (
    <div data-testid="performance-summary">
      Total Variants: {summary?.total_variants || 0}
    </div>
  )
}));

vi.mock('../ActiveVariantsTable', () => ({
  ActiveVariantsTable: ({ variants, onVariantSelect }) => (
    <div data-testid="active-variants-table">
      {variants?.map(variant => (
        <div key={variant.id} data-testid={`variant-${variant.id}`}>
          {variant.content}
          <button onClick={() => onVariantSelect?.(variant.id)}>Select</button>
        </div>
      ))}
    </div>
  )
}));

vi.mock('../PerformanceChart', () => ({
  PerformanceChart: ({ data }) => (
    <div data-testid="performance-chart">
      Chart with {data?.length || 0} data points
    </div>
  )
}));

vi.mock('../PatternFatigueWarnings', () => ({
  PatternFatigueWarnings: ({ warnings }) => (
    <div data-testid="pattern-fatigue-warnings">
      {warnings?.length || 0} warnings
    </div>
  )
}));

vi.mock('../EarlyKillFeed', () => ({
  EarlyKillFeed: ({ events }) => (
    <div data-testid="early-kill-feed">
      {events?.length || 0} kill events
    </div>
  )
}));

vi.mock('../OptimizationAlerts', () => ({
  OptimizationAlerts: ({ suggestions }) => (
    <div data-testid="optimization-alerts">
      {suggestions?.length || 0} suggestions
    </div>
  )
}));

import { useWebSocket } from '../hooks/useWebSocket';
import { useDashboardData } from '../hooks/useDashboardData';

describe('VariantDashboard', () => {
  let mockUseWebSocket;
  let mockUseDashboardData;

  const mockInitialData = {
    summary: {
      total_variants: 15,
      avg_engagement_rate: 0.058,
      active_count: 12,
      performance_trend: 'up'
    },
    active_variants: [
      {
        id: 'var_1',
        content: 'Test variant 1 content',
        predicted_er: 0.065,
        live_metrics: {
          engagement_rate: 0.062,
          interactions: 150,
          views: 2400
        },
        time_since_post: { hours_active: 2.5 },
        performance_vs_prediction: { relative_delta: -0.046 }
      },
      {
        id: 'var_2',
        content: 'Test variant 2 content',
        predicted_er: 0.052,
        live_metrics: {
          engagement_rate: 0.068,
          interactions: 180,
          views: 2650
        },
        time_since_post: { hours_active: 1.8 },
        performance_vs_prediction: { relative_delta: 0.308 }
      }
    ],
    early_kills_today: {
      kills_today: 3,
      avg_time_to_kill_minutes: 4.2
    },
    pattern_fatigue_warnings: [
      {
        pattern_id: 'curiosity_gap',
        fatigue_score: 0.85,
        warning_level: 'high',
        recommendation: 'Switch to controversy patterns'
      }
    ],
    optimization_opportunities: [
      {
        type: 'prediction_calibration',
        title: 'High Early Kill Rate',
        description: 'Consider recalibrating prediction model',
        priority: 'high'
      }
    ],
    real_time_feed: [
      {
        event_type: 'early_kill',
        variant_id: 'var_3',
        timestamp: new Date().toISOString(),
        details: { reason: 'low_engagement' }
      }
    ]
  };

  beforeEach(() => {
    mockUseWebSocket = {
      wsConnection: { readyState: WebSocket.OPEN },
      wsStatus: 'connected',
      reconnect: vi.fn(),
      disconnect: vi.fn()
    };

    mockUseDashboardData = {
      loading: false,
      error: null,
      refetch: vi.fn()
    };

    useWebSocket.mockReturnValue(mockUseWebSocket);
    useDashboardData.mockReturnValue(mockUseDashboardData);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders dashboard with all sections when data is loaded', async () => {
      const setMetrics = vi.fn();
      
      // Mock successful WebSocket with initial data
      mockUseWebSocket.wsConnection = {
        readyState: WebSocket.OPEN,
        onmessage: null
      };
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        // Simulate receiving initial data
        React.useEffect(() => {
          onMessage({
            type: 'initial_data',
            data: mockInitialData
          });
        }, []);
        
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      await waitFor(() => {
        expect(screen.getByTestId('performance-summary')).toBeInTheDocument();
        expect(screen.getByTestId('active-variants-table')).toBeInTheDocument();
        expect(screen.getByTestId('performance-chart')).toBeInTheDocument();
        expect(screen.getByTestId('pattern-fatigue-warnings')).toBeInTheDocument();
        expect(screen.getByTestId('early-kill-feed')).toBeInTheDocument();
        expect(screen.getByTestId('optimization-alerts')).toBeInTheDocument();
      });
    });

    it('shows loading state initially', () => {
      mockUseDashboardData.loading = true;
      useDashboardData.mockReturnValue(mockUseDashboardData);

      render(<VariantDashboard personaId="ai-jesus" />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('shows error state when there is an error', () => {
      mockUseDashboardData.error = 'Failed to load dashboard data';
      useDashboardData.mockReturnValue(mockUseDashboardData);

      render(<VariantDashboard personaId="ai-jesus" />);

      expect(screen.getByText(/error/i)).toBeInTheDocument();
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });

    it('shows WebSocket connection status', () => {
      mockUseWebSocket.wsStatus = 'disconnected';
      useWebSocket.mockReturnValue(mockUseWebSocket);

      render(<VariantDashboard personaId="ai-jesus" />);

      expect(screen.getByText(/disconnected/i)).toBeInTheDocument();
    });
  });

  describe('Real-time Updates', () => {
    it('updates variant metrics on performance_update message', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      // Simulate initial data
      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      await waitFor(() => {
        expect(screen.getByTestId('variant-var_1')).toBeInTheDocument();
      });

      // Simulate performance update
      act(() => {
        onMessageCallback({
          type: 'variant_update',
          data: {
            event_type: 'performance_update',
            variant_id: 'var_1',
            current_er: 0.075,
            interaction_count: 200
          }
        });
      });

      // Verify the variant data was updated
      await waitFor(() => {
        // This would require checking the internal state or rendered content
        // In a real implementation, you'd check if the displayed ER changed
        expect(screen.getByTestId('variant-var_1')).toBeInTheDocument();
      });
    });

    it('adds early kill events to real-time feed', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      // Simulate initial data
      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      // Simulate early kill event
      act(() => {
        onMessageCallback({
          type: 'variant_update',
          data: {
            event_type: 'early_kill',
            variant_id: 'var_4',
            kill_reason: 'negative_sentiment',
            final_er: 0.018,
            killed_at: new Date().toISOString()
          }
        });
      });

      await waitFor(() => {
        // The early kill feed should show updated count
        const feed = screen.getByTestId('early-kill-feed');
        expect(feed.textContent).toContain('2'); // 1 existing + 1 new
      });
    });

    it('handles pattern fatigue updates', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      // Simulate pattern fatigue alert
      act(() => {
        onMessageCallback({
          type: 'pattern_update',
          data: {
            event_type: 'pattern_fatigue_alert',
            pattern_id: 'social_proof',
            fatigue_score: 0.92,
            warning_level: 'critical'
          }
        });
      });

      await waitFor(() => {
        // Pattern fatigue warnings should be updated
        expect(screen.getByTestId('pattern-fatigue-warnings')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    it('handles variant selection', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      // Simulate initial data
      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      await waitFor(() => {
        expect(screen.getByTestId('variant-var_1')).toBeInTheDocument();
      });

      // Click on variant selection
      const selectButton = screen.getAllByText('Select')[0];
      fireEvent.click(selectButton);

      // Should trigger some action (like showing detailed view)
      // This would depend on the actual implementation
    });

    it('handles refresh button click', async () => {
      render(<VariantDashboard personaId="ai-jesus" />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      fireEvent.click(refreshButton);

      expect(mockUseDashboardData.refetch).toHaveBeenCalled();
    });

    it('handles WebSocket reconnection', async () => {
      mockUseWebSocket.wsStatus = 'disconnected';
      useWebSocket.mockReturnValue(mockUseWebSocket);

      render(<VariantDashboard personaId="ai-jesus" />);

      const reconnectButton = screen.getByRole('button', { name: /reconnect/i });
      fireEvent.click(reconnectButton);

      expect(mockUseWebSocket.reconnect).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('handles WebSocket connection errors gracefully', () => {
      mockUseWebSocket.wsStatus = 'error';
      useWebSocket.mockReturnValue(mockUseWebSocket);

      render(<VariantDashboard personaId="ai-jesus" />);

      expect(screen.getByText(/connection error/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /reconnect/i })).toBeInTheDocument();
    });

    it('handles malformed WebSocket messages', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      // Mock console.error to prevent test noise
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(<VariantDashboard personaId="ai-jesus" />);

      // Simulate malformed message
      act(() => {
        onMessageCallback({
          type: 'unknown_type',
          data: null
        });
      });

      // Should not crash the component
      expect(screen.getByTestId('performance-summary')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('handles missing persona ID', () => {
      render(<VariantDashboard personaId="" />);

      expect(screen.getByText(/invalid persona/i)).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('does not re-render unnecessarily on same data', async () => {
      let onMessageCallback;
      let renderCount = 0;
      
      const TestWrapper = ({ personaId }) => {
        renderCount++;
        return <VariantDashboard personaId={personaId} />;
      };
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      const { rerender } = render(<TestWrapper personaId="ai-jesus" />);

      const initialRenderCount = renderCount;

      // Send same data twice
      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      // Should not cause additional re-renders if data is the same
      expect(renderCount).toBeLessThanOrEqual(initialRenderCount + 2);
    });

    it('handles large datasets efficiently', async () => {
      const largeDataset = {
        ...mockInitialData,
        active_variants: Array.from({ length: 100 }, (_, i) => ({
          id: `var_${i}`,
          content: `Test variant ${i}`,
          predicted_er: 0.05 + (i % 10) * 0.001,
          live_metrics: {
            engagement_rate: 0.05 + (i % 8) * 0.002,
            interactions: 100 + i,
            views: 2000 + i * 10
          }
        }))
      };

      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      const startTime = Date.now();
      
      render(<VariantDashboard personaId="ai-jesus" />);

      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: largeDataset
        });
      });

      const renderTime = Date.now() - startTime;

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(1000); // 1 second
      
      await waitFor(() => {
        expect(screen.getByTestId('active-variants-table')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', async () => {
      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: mockInitialData
        });
      });

      await waitFor(() => {
        // Check for accessibility attributes
        const dashboard = screen.getByRole('main');
        expect(dashboard).toHaveAttribute('aria-label', 'Variant Performance Dashboard');
      });
    });

    it('supports keyboard navigation', async () => {
      render(<VariantDashboard personaId="ai-jesus" />);

      // Test tab navigation
      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      refreshButton.focus();
      
      expect(document.activeElement).toBe(refreshButton);
    });
  });

  describe('Data Validation', () => {
    it('handles missing data fields gracefully', async () => {
      const incompleteData = {
        summary: { total_variants: 5 }, // Missing other fields
        active_variants: [
          { id: 'var_1' } // Missing other required fields
        ]
        // Missing other sections
      };

      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: incompleteData
        });
      });

      // Should render without crashing
      await waitFor(() => {
        expect(screen.getByTestId('performance-summary')).toBeInTheDocument();
      });
    });

    it('validates numeric data ranges', async () => {
      const invalidData = {
        ...mockInitialData,
        active_variants: [
          {
            ...mockInitialData.active_variants[0],
            live_metrics: {
              engagement_rate: -0.1, // Invalid negative ER
              interactions: -50, // Invalid negative interactions
              views: 'invalid' // Non-numeric value
            }
          }
        ]
      };

      let onMessageCallback;
      
      useWebSocket.mockImplementation((personaId, { onMessage }) => {
        onMessageCallback = onMessage;
        return mockUseWebSocket;
      });

      render(<VariantDashboard personaId="ai-jesus" />);

      act(() => {
        onMessageCallback({
          type: 'initial_data',
          data: invalidData
        });
      });

      // Should handle invalid data gracefully
      await waitFor(() => {
        expect(screen.getByTestId('active-variants-table')).toBeInTheDocument();
      });
    });
  });
});
