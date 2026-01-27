// frontend/lib/websocket/websocket-manager.ts

import { EventEmitter } from 'events';

interface WebSocketConfig {
  url: string;
  token: string;
  maxReconnectAttempts?: number;
  reconnectBaseDelay?: number;
  heartbeatInterval?: number;
  heartbeatTimeout?: number;
}

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  [key: string]: any;
}

export class WebSocketManager extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private isManualDisconnect = false;
  private messageQueue: WebSocketMessage[] = [];

  constructor(config: WebSocketConfig) {
    super();
    this.config = {
      maxReconnectAttempts: 5,
      reconnectBaseDelay: 1000,
      heartbeatInterval: 30000,
      heartbeatTimeout: 10000,
      ...config,
    };
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected');
      return;
    }

    this.isManualDisconnect = false;
    const wsUrl = `${this.config.url}?token=${this.config.token}`;
    
    this.ws = new WebSocket(wsUrl);
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connected');
      this.startHeartbeat();
      this.flushMessageQueue();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    };

    this.ws.onclose = (event) => {
      console.log(`WebSocket closed: ${event.code} - ${event.reason}`);
      this.cleanup();
      this.emit('disconnected', event);

      if (!this.isManualDisconnect) {
        this.scheduleReconnect();
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    switch (message.type) {
      case 'connection_established':
        this.emit('connected', message.data);
        break;

      case 'query_update':
        this.emit('query_update', message.data);
        break;

      case 'workflow_update':
        this.emit('workflow_update', message.data);
        break;

      case 'subscription_confirmed':
        this.emit('subscription_confirmed', message.data);
        break;

      case 'heartbeat':
        this.resetHeartbeatTimeout();
        break;

      case 'ping':
        this.sendPong();
        break;

      case 'error':
        this.emit('server_error', message.data);
        break;

      default:
        this.emit('message', message);
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'heartbeat',
          timestamp: new Date().toISOString(),
        }));
        this.scheduleHeartbeatTimeout();
      }
    }, this.config.heartbeatInterval);
  }

  private scheduleHeartbeatTimeout(): void {
    this.heartbeatTimeout = setTimeout(() => {
      console.warn('Heartbeat timeout - connection may be stale');
      this.scheduleReconnect();
    }, this.config.heartbeatTimeout);
  }

  private resetHeartbeatTimeout(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= (this.config.maxReconnectAttempts || 5)) {
      console.error('Max reconnect attempts reached');
      this.emit('reconnect_failed');
      return;
    }

    this.reconnectAttempts++;
    const delay = (this.config.reconnectBaseDelay || 1000) * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private sendPong(): void {
    this.send({ type: 'pong', timestamp: new Date().toISOString() });
  }

  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  send(message: Record<string, any>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.messageQueue.push(message as WebSocketMessage);
    }
  }

  subscribeToQuery(queryId: string): void {
    this.send({
      type: 'subscribe_query',
      queryId,
      timestamp: new Date().toISOString(),
    });
  }

  unsubscribeFromQuery(queryId: string): void {
    this.send({
      type: 'unsubscribe_query',
      queryId,
      timestamp: new Date().toISOString(),
    });
  }

  submitQuery(query: string, operation: string = 'general'): void {
    this.send({
      type: 'submit_query',
      query,
      operation,
      timestamp: new Date().toISOString(),
    });
  }

  disconnect(): void {
    this.isManualDisconnect = true;
    this.cleanup();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  private cleanup(): void {
    this.resetHeartbeatTimeout();
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
