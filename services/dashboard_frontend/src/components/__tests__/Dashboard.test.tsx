/**
 * Tests for main Dashboard component.
 * Following TDD - write failing tests first.
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Dashboard } from '../Dashboard';

// Mock WebSocket
const mockWebSocket = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
  readyState: WebSocket.OPEN
};

// Mock global WebSocket
(global as any).WebSocket = jest.fn(() => mockWebSocket);

describe('Dashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock fetch for initial data load
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          variants: [
            {
              variant_id: 'test_variant',
              engagement_rate: 0.15,
              impressions: 100,
              successes: 15,
              early_kill_status: 'monitoring',
              pattern_fatigue_warning: false,
              freshness_score: 0.8
            }
          ]
        })
      })
    ) as jest.Mock;
  });

  test('renders dashboard title', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Real-Time Variant Performance Dashboard')).toBeInTheDocument();
  });

  test('establishes WebSocket connection on mount', () => {
    render(<Dashboard />);
    
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/dashboard/ws');
  });

  test('fetches initial variant data', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/dashboard/variants');
    });
  });

  test('displays loading state initially', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Loading variant data...')).toBeInTheDocument();
  });

  test('displays variant data after loading', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('test_variant')).toBeInTheDocument();
    });
  });

  test('handles WebSocket messages for real-time updates', async () => {
    render(<Dashboard />);
    
    // Simulate WebSocket message
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify({
        type: 'metrics_update',
        variant_id: 'test_variant',
        new_engagement_rate: 0.20
      })
    });
    
    // Get the message handler that was registered
    const messageHandler = mockWebSocket.addEventListener.mock.calls
      .find(call => call[0] === 'message')[1];
    
    // Call the handler
    messageHandler(messageEvent);
    
    await waitFor(() => {
      // Should update the display with new engagement rate
      expect(screen.getByText('20.0%')).toBeInTheDocument();
    });
  });

  test('shows connection status indicator', () => {
    render(<Dashboard />);
    
    expect(screen.getByText(/Connection:/)).toBeInTheDocument();
  });
});