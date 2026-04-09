import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
    isConnected: boolean;
    lastMessage: any;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { user } = useAuth();
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState<any>(null);
    const socketRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<number | null>(null);

    const connect = () => {
        if (!user) return;

        // Use the same host as the API, but with ws:// or wss://
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001';
        const wsUrl = apiUrl.replace(/^http/, 'ws') + '/ws/alerts';

        console.log(`Connecting to WebSocket: ${wsUrl}`);
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
            console.log('WebSocket connected ✓');
            setIsConnected(true);
            if (reconnectTimeoutRef.current) {
                window.clearTimeout(reconnectTimeoutRef.current);
                reconnectTimeoutRef.current = null;
            }
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                setLastMessage(data);
                handleIncomingMessage(data);
            } catch (err) {
                console.error('Failed to parse WS message:', err);
            }
        };

        socket.onclose = () => {
            console.log('WebSocket disconnected. Attempting reconnect...');
            setIsConnected(false);
            // Reconnect logic
            reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
            socket.close();
        };
    };

    const handleIncomingMessage = (data: any) => {
        if (data.type === 'SAFETY_ALERT') {
            const severityColor = 
                data.severity === 'HIGH' ? '#ef4444' : 
                data.severity === 'MEDIUM' ? '#f97316' : '#3b82f6';

            toast.error(
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ fontWeight: 700, color: severityColor }}>
                        {data.severity} SEVERITY ALERT
                    </div>
                    <div style={{ fontSize: '0.8rem' }}>{data.message}</div>
                </div>,
                { duration: 6000 }
            );
        }
    };

    useEffect(() => {
        if (user) {
            connect();
        } else {
            if (socketRef.current) {
                socketRef.current.close();
            }
        }

        return () => {
            if (socketRef.current) {
                socketRef.current.close();
            }
            if (reconnectTimeoutRef.current) {
                window.clearTimeout(reconnectTimeoutRef.current);
            }
        };
    }, [user]);

    return (
        <WebSocketContext.Provider value={{ isConnected, lastMessage }}>
            {children}
        </WebSocketContext.Provider>
    );
};

export const useWebSocket = () => {
    const context = useContext(WebSocketContext);
    if (context === undefined) {
        throw new Error('useWebSocket must be used within a WebSocketProvider');
    }
    return context;
};
