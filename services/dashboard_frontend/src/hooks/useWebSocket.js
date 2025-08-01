import { useState, useEffect, useRef } from 'react';

export function useWebSocket(personaId, { onMessage, onError, reconnectInterval = 5000 }) {
    const [wsConnection, setWsConnection] = useState(null);
    const [wsStatus, setWsStatus] = useState('disconnected');
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    useEffect(() => {
        if (!personaId) return;

        const connect = () => {
            try {
                const wsUrl = `ws://localhost:8081/dashboard/ws/${personaId}`;
                const ws = new WebSocket(wsUrl);

                ws.onopen = () => {
                    console.log('WebSocket connected');
                    setWsStatus('connected');
                    setWsConnection(ws);
                    wsRef.current = ws;
                    
                    // Clear any reconnection timeout
                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                        reconnectTimeoutRef.current = null;
                    }
                };

                ws.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        if (onMessage) {
                            onMessage(message);
                        }
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    setWsStatus('error');
                    if (onError) {
                        onError(error);
                    }
                };

                ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    setWsStatus('disconnected');
                    setWsConnection(null);
                    wsRef.current = null;
                    
                    // Schedule reconnection
                    reconnectTimeoutRef.current = setTimeout(() => {
                        console.log('Attempting to reconnect...');
                        setWsStatus('reconnecting');
                        connect();
                    }, reconnectInterval);
                };

            } catch (error) {
                console.error('Error creating WebSocket:', error);
                setWsStatus('error');
            }
        };

        connect();

        // Cleanup function
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [personaId, onMessage, onError, reconnectInterval]);

    const sendMessage = (message) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected, cannot send message');
        }
    };

    return {
        wsConnection,
        wsStatus,
        sendMessage
    };
}