'use client';

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/lib/stores/useAuthStore';
import { useSystemStore } from '@/lib/stores/useSystemStore';
import { useQueryStore } from '@/lib/stores/useQueryStore';
import { WebSocketMessage, WebSocketMessageType } from '@/types';

interface WebSocketContextType {
  isConnected: boolean;
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  connectionQuality: 'excellent' | 'good' | 'poor' | 'disconnected';
  reconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionQuality, setConnectionQuality] = useState<
    'excellent' | 'good' | 'poor' | 'disconnected'
  >('disconnected');
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout>();
  const messageQueueRef = useRef<any[]>([]);
  
  const { token } = useAuthStore();
  const { setSystemStatus, updateModelStatus, setConnected, setConnectionQuality } = useSystemStore();
  const { updateQueryStatus, appendResponseChunk } = useQueryStore();

  const MAX_RECONNECT_ATTEMPTS = 5;
  const BASE_RECONNECT_DELAY = 1000;
  const PING_INTERVAL = 30000;
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

  const processMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'query_update': {
        const { queryId, status, chunk, complete, responseText } = message.data;
        
        if (status) {
          updateQueryStatus(queryId, status);
        }
        
        if (chunk) {
          appendResponseChunk(queryId, chunk);
        }
        
        if (complete) {
          updateQueryStatus(queryId, 'completed');
        }
        break;
      }
      
      case 'system_status': {
        setSystemStatus(message.data);
        break;
      }
      
      case 'model_status': {
        updateModelStatus(message.data);
        break;
      }
      
      case 'pong': {
        const latency = Date.now() - parseInt(message.timestamp);
        if (latency < 100) {
          setConnectionQuality('excellent');
        } else if (latency < 300) {
          setConnectionQuality('good');
        } else {
          setConnectionQuality('poor');
        }
        break;
      }
    }
  }, [setSystemStatus, updateModelStatus, updateQueryStatus, appendResponseChunk]);

  const connect = useCallback(() => {
    if (!token) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = `${WS_URL}/v1/ws`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnected(true);
        setConnectionQuality('excellent');
        reconnectAttempts.current = 0;

        // Send authentication
        wsRef.current?.send(
          JSON.stringify({
            type: 'auth',
            token,
          })
        );

        // Process any queued messages
        while (messageQueueRef.current.length > 0) {
          const msg = messageQueueRef.current.shift();
          wsRef.current?.send(JSON.stringify(msg));
        }

        // Start heartbeat
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(
              JSON.stringify({
                type: 'ping',
                timestamp: Date.now().toString(),
              })
            );
          }
        }, PING_INTERVAL);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          processMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionQuality('poor');
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        setConnected(false);
        setConnectionQuality('disconnected');

        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
        }

        // Attempt reconnection if not intentionally closed
        if (event.code !== 1000 && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts.current);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setConnectionQuality('disconnected');
    }
  }, [token, setConnected, setConnectionQuality, setSystemStatus, updateModelStatus, processMessage]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      // Queue message for later
      messageQueueRef.current.push(message);
      console.warn('WebSocket not connected, message queued');
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reconnectAttempts.current = 0;
    wsRef.current?.close();
    connect();
  }, [connect]);

  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      wsRef.current?.close(1000, 'Client closing');
    };
  }, [token, connect]);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        sendMessage,
        lastMessage,
        connectionQuality,
        reconnect,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
}
