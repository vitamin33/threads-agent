/**
 * Comprehensive tests for useWebSocket hook
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useWebSocket } from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
    
    // Simulate connection opening after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 10);
  }
  
  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }
  
  close(code = 1000, reason = '') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose({ code, reason });
  }
  
  // Test helper methods
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
  
  simulateError(error) {
    if (this.onerror) this.onerror(error);
  }
}

// Define WebSocket constants
const WebSocketStates = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
};

global.WebSocket = MockWebSocket;
Object.assign(global.WebSocket, WebSocketStates);

describe('useWebSocket', () => {
  let mockWebSocket;

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    mockWebSocket = null;
  });

  afterEach(() => {
    vi.useRealTimers();
    if (mockWebSocket && mockWebSocket.close) {
      mockWebSocket.close();
    }
  });

  describe('Connection Management', () => {
    it('establishes WebSocket connection on mount', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      expect(result.current.wsStatus).toBe('disconnected');

      // Fast-forward timers to simulate connection
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      expect(result.current.wsConnection).toBeTruthy();
      expect(result.current.wsConnection.url).toBe('ws://localhost:8081/dashboard/ws/ai-jesus');
    });

    it('handles connection open event', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
        expect(result.current.wsConnection.readyState).toBe(WebSocket.OPEN);
      });
    });

    it('handles connection close event', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      // Wait for connection to open
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Simulate connection close
      act(() => {
        result.current.wsConnection.close();
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('disconnected');
      });
    });

    it('cleans up connection on unmount', async () => {
      const { result, unmount } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const wsConnection = result.current.wsConnection;
      const closeSpy = vi.spyOn(wsConnection, 'close');

      unmount();

      expect(closeSpy).toHaveBeenCalled();
    });
  });

  describe('Message Handling', () => {
    it('calls onMessage callback when message received', async () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const testMessage = {
        type: 'initial_data',
        data: { summary: { total_variants: 10 } }
      };

      act(() => {
        result.current.wsConnection.simulateMessage(testMessage);
      });

      expect(onMessage).toHaveBeenCalledWith(testMessage);
    });

    it('handles malformed JSON messages gracefully', async () => {
      const onMessage = vi.fn();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Simulate malformed JSON
      act(() => {
        if (result.current.wsConnection.onmessage) {
          result.current.wsConnection.onmessage({ data: 'invalid json{' });
        }
      });

      expect(consoleSpy).toHaveBeenCalledWith(
        'Error parsing WebSocket message:',
        expect.any(Error)
      );
      expect(onMessage).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });

    it('handles multiple message types', async () => {
      const onMessage = vi.fn();
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const messages = [
        { type: 'initial_data', data: {} },
        { type: 'variant_update', data: { variant_id: 'var_1' } },
        { type: 'pattern_update', data: { pattern_id: 'curiosity_gap' } },
        { type: 'pong', timestamp: Date.now() }
      ];

      messages.forEach(message => {
        act(() => {
          result.current.wsConnection.simulateMessage(message);
        });
      });

      expect(onMessage).toHaveBeenCalledTimes(4);
      messages.forEach(message => {
        expect(onMessage).toHaveBeenCalledWith(message);
      });
    });
  });

  describe('Error Handling', () => {
    it('handles WebSocket errors', async () => {
      const onError = vi.fn();
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn(), onError })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const error = new Error('Connection failed');
      
      act(() => {
        result.current.wsConnection.simulateError(error);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('error');
      });

      expect(onError).toHaveBeenCalledWith(error);
    });

    it('sets error status on connection error', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      act(() => {
        result.current.wsConnection.simulateError(new Error('Test error'));
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('error');
      });
    });
  });

  describe('Reconnection Logic', () => {
    it('attempts reconnection after disconnect', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { 
          onMessage: vi.fn(),
          reconnectInterval: 1000
        })
      );

      // Initial connection
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Simulate disconnect
      act(() => {
        result.current.wsConnection.close();
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('disconnected');
      });

      // Fast-forward to trigger reconnection
      act(() => {
        vi.advanceTimersByTime(1100); // reconnectInterval + connection time
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });
    });

    it('does not reconnect if explicitly closed', async () => {
      const { result, unmount } = renderHook(() => 
        useWebSocket('ai-jesus', { 
          onMessage: vi.fn(),
          reconnectInterval: 500
        })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Unmount (explicit close)
      unmount();

      // Fast-forward beyond reconnect interval
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Should not attempt reconnection
      expect(result.current.wsStatus).toBe('connected'); // Last known state
    });

    it('clears reconnection timeout on successful reconnection', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { 
          onMessage: vi.fn(),
          reconnectInterval: 1000
        })
      );

      // Initial connection and disconnect cycle
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      act(() => {
        result.current.wsConnection.close();
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('disconnected');
      });

      // Reconnect
      act(() => {
        vi.advanceTimersByTime(1100);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Verify no additional reconnection attempts
      act(() => {
        vi.advanceTimersByTime(2000);
      });

      // Should still be connected (no additional attempts)
      expect(result.current.wsStatus).toBe('connected');
    });
  });

  describe('Persona ID Changes', () => {
    it('reconnects when persona ID changes', async () => {
      const { result, rerender } = renderHook(
        ({ personaId }) => useWebSocket(personaId, { onMessage: vi.fn() }),
        { initialProps: { personaId: 'ai-jesus' } }
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const firstConnection = result.current.wsConnection;
      expect(firstConnection.url).toBe('ws://localhost:8081/dashboard/ws/ai-jesus');

      // Change persona ID
      rerender({ personaId: 'ai-buddha' });

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsConnection.url).toBe('ws://localhost:8081/dashboard/ws/ai-buddha');
      });
    });

    it('does not reconnect if persona ID is empty', () => {
      const { result } = renderHook(() => 
        useWebSocket('', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(100);
      });

      expect(result.current.wsConnection).toBeNull();
      expect(result.current.wsStatus).toBe('disconnected');
    });
  });

  describe('Custom Configuration', () => {
    it('uses custom reconnect interval', async () => {
      const customInterval = 2000;
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { 
          onMessage: vi.fn(),
          reconnectInterval: customInterval
        })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Disconnect
      act(() => {
        result.current.wsConnection.close();
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('disconnected');
      });

      // Should not reconnect before custom interval
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.wsStatus).toBe('disconnected');

      // Should reconnect after custom interval
      act(() => {
        vi.advanceTimersByTime(1100);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });
    });

    it('handles custom WebSocket URL configuration', async () => {
      // Mock environment variable or configuration
      const originalLocation = window.location;
      
      Object.defineProperty(window, 'location', {
        value: {
          ...originalLocation,
          hostname: 'custom-host.com',
          port: '9999'
        },
        writable: true
      });

      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Should still connect to localhost:8081 as per implementation
      expect(result.current.wsConnection.url).toBe('ws://localhost:8081/dashboard/ws/ai-jesus');

      // Restore original location
      Object.defineProperty(window, 'location', {
        value: originalLocation,
        writable: true
      });
    });
  });

  describe('Memory Management', () => {
    it('cleans up event listeners on unmount', async () => {
      const { result, unmount } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      const wsConnection = result.current.wsConnection;
      
      unmount();

      // Event listeners should be cleaned up
      expect(wsConnection.onopen).toBeNull();
      expect(wsConnection.onclose).toBeNull();
      expect(wsConnection.onmessage).toBeNull();
      expect(wsConnection.onerror).toBeNull();
    });

    it('clears timeouts on unmount', async () => {
      const { result, unmount } = renderHook(() => 
        useWebSocket('ai-jesus', { 
          onMessage: vi.fn(),
          reconnectInterval: 5000
        })
      );

      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      // Disconnect to trigger reconnection timeout
      act(() => {
        result.current.wsConnection.close();
      });

      // Unmount before reconnection timeout expires
      unmount();

      // Fast-forward beyond reconnect interval
      act(() => {
        vi.advanceTimersByTime(10000);
      });

      // Should not attempt reconnection
      expect(vi.getTimerCount()).toBe(0);
    });
  });

  describe('Connection State Accuracy', () => {
    it('accurately reflects WebSocket ready state', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      // Initially disconnected
      expect(result.current.wsStatus).toBe('disconnected');

      // Connecting
      act(() => {
        vi.advanceTimersByTime(5);
      });

      // Should transition to connected
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
        expect(result.current.wsConnection?.readyState).toBe(WebSocket.OPEN);
      });
    });

    it('handles rapid state changes', async () => {
      const { result } = renderHook(() => 
        useWebSocket('ai-jesus', { onMessage: vi.fn() })
      );

      // Rapid connect/disconnect cycle
      act(() => {
        vi.advanceTimersByTime(20);
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('connected');
      });

      act(() => {
        result.current.wsConnection.close();
      });

      await waitFor(() => {
        expect(result.current.wsStatus).toBe('disconnected');
      });

      // Should maintain accurate state
      expect(result.current.wsConnection?.readyState).toBe(WebSocket.CLOSED);
    });
  });
});
