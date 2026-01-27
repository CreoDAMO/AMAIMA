// src/types/index.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface ApiResponse<T = any> {
  user?: User;
  access_token?: string;
  refresh_token?: string;
  data?: T;
  success?: boolean;
  error?: {
    code: string;
    message: string;
    type?: string;
    details?: any;
  };
  meta?: {
    requestId: string;
    timestamp: string;
  };
}

export interface Query {
  id: string;
  query: string;
  responseText: string;
  modelUsed: string;
  latencyMs: number;
  confidence: number;
  status: string;
  timestamp: string;
}

export type WebSocketMessageType = 'query_update' | 'system_status' | 'model_status' | 'pong' | 'auth' | 'connection_established' | 'workflow_update' | 'subscription_confirmed' | 'heartbeat' | 'ping' | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
}
