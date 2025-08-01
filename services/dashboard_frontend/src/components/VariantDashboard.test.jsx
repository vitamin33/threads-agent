import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { VariantDashboard } from './VariantDashboard';

// Mock the hooks
vi.mock('../hooks/useWebSocket', () => ({
    useWebSocket: vi.fn(() => ({
        wsConnection: {},
        wsStatus: 'connected',
        sendMessage: vi.fn()
    }))
}));

vi.mock('../hooks/useDashboardData', () => ({
    useDashboardData: vi.fn(() => ({
        loading: false,
        error: null,
        refetch: vi.fn()
    }))
}));

describe('VariantDashboard', () => {
    const mockMetrics = {
        summary: {
            total_variants: 10,
            avg_engagement_rate: 0.065
        },
        active_variants: [
            {
                id: 'var_1',
                content: 'Test variant content that is longer than 50 characters to test truncation',
                predicted_er: 0.06,
                live_metrics: {
                    engagement_rate: 0.058,
                    interactions: 120
                },
                performance_vs_prediction: -0.033,
                time_since_post: '2h',
                status: 'active'
            }
        ],
        optimization_opportunities: [
            {
                type: 'high_kill_rate',
                priority: 'high',
                title: 'High Early Kill Rate',
                description: '35% of variants killed early'
            }
        ],
        pattern_fatigue_warnings: [],
        early_kills_today: { kills_today: 3 },
        real_time_feed: []
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    test('renders dashboard with persona ID', () => {
        render(<VariantDashboard personaId="ai-jesus" />);
        
        expect(screen.getByText(/Variant Performance Dashboard - ai-jesus/i)).toBeInTheDocument();
    });

    test('displays connection status', () => {
        render(<VariantDashboard personaId="ai-jesus" />);
        
        expect(screen.getByText(/Status:/)).toBeInTheDocument();
        expect(screen.getByText(/connected/)).toBeInTheDocument();
    });

    test('shows loading state', () => {
        const { useDashboardData } = vi.mocked(await import('../hooks/useDashboardData'));
        useDashboardData.mockReturnValue({
            loading: true,
            error: null,
            refetch: vi.fn()
        });

        render(<VariantDashboard personaId="ai-jesus" />);
        
        expect(screen.getByText(/Loading dashboard.../)).toBeInTheDocument();
    });

    test('shows error state with retry button', () => {
        const mockRefetch = vi.fn();
        const { useDashboardData } = vi.mocked(await import('../hooks/useDashboardData'));
        useDashboardData.mockReturnValue({
            loading: false,
            error: new Error('Failed to fetch'),
            refetch: mockRefetch
        });

        render(<VariantDashboard personaId="ai-jesus" />);
        
        expect(screen.getByText(/Error loading dashboard: Failed to fetch/)).toBeInTheDocument();
        expect(screen.getByText(/Retry/)).toBeInTheDocument();
    });

    test('updates metrics when WebSocket message received', async () => {
        let onMessageCallback;
        const { useWebSocket } = vi.mocked(await import('../hooks/useWebSocket'));
        useWebSocket.mockImplementation((personaId, { onMessage }) => {
            onMessageCallback = onMessage;
            return {
                wsConnection: {},
                wsStatus: 'connected',
                sendMessage: vi.fn()
            };
        });

        const { rerender } = render(<VariantDashboard personaId="ai-jesus" />);

        // Simulate receiving initial data
        onMessageCallback({
            type: 'initial_data',
            data: mockMetrics
        });

        await waitFor(() => {
            expect(screen.getByText(/Active Variants/)).toBeInTheDocument();
        });
    });
});