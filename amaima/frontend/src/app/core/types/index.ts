// Query Types
export interface Query {
  id: string;
  userId: string;
  queryText: string;
  responseText?: string;
  operation: QueryOperation;
  status: QueryStatus;
  modelUsed?: string;
  confidence?: number;
  latencyMs?: number;
  createdAt: string;
  completedAt?: string;
  metadata?: QueryMetadata;
}

export type QueryOperation = 'general' | 'code_generation' | 'analysis' | 'translation' | 'creative';

export type QueryStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface QueryMetadata {
  tokensInput?: number;
  tokensOutput?: number;
  complexity?: 'TRIVIAL' | 'SIMPLE' | 'MODERATE' | 'COMPLEX' | 'EXPERT';
  suggestedModel?: string;
}

export interface QuerySubmitRequest {
  query: string;
  operation: QueryOperation;
  preferences?: QueryPreferences;
}

export interface QueryPreferences {
  streaming?: boolean;
  modelId?: string;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

// Workflow Types
export interface Workflow {
  id: string;
  userId: string;
  name: string;
  description?: string;
  steps: WorkflowStep[];
  status: WorkflowStatus;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowStep {
  id: string;
  stepType: 'query' | 'condition' | 'loop' | 'function' | 'api_call';
  parameters: Record<string, any>;
  dependencies?: string[];
  nextSteps?: string[];
}

export type WorkflowStatus = 'draft' | 'running' | 'completed' | 'failed';

// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: UserRole;
  preferences: UserPreferences;
  createdAt: string;
}

export type UserRole = 'user' | 'admin' | 'premium';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  defaultModel?: string;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  queryComplete: boolean;
  systemUpdates: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiErrorInterface;
  meta?: ResponseMeta;
}

export interface ApiErrorInterface {
  code: string;
  message: string;
  path?: string;
  requestId?: string;
  details?: Record<string, any>;
}

export interface ResponseMeta {
  requestId: string;
  timestamp: string;
  rateLimit?: RateLimitInfo;
}

export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetAt: string;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: WebSocketMessageType;
  data: any;
  timestamp: string;
}

export type WebSocketMessageType = 
  | 'query_update'
  | 'workflow_update'
  | 'system_status'
  | 'auth_confirm'
  | 'ping'
  | 'pong';

export interface QueryUpdateData {
  queryId: string;
  status: QueryStatus;
  chunk?: string;
  complete?: boolean;
  responseText?: string;
}

export interface SystemStatusData {
  cpuUsage: number;
  memoryUsage: number;
  activeQueries: number;
  queriesPerMinute: number;
  modelStatus: ModelStatus[];
}

export interface ModelStatus {
  modelId: string;
  name: string;
  status: 'ready' | 'loading' | 'error';
  loadProgress?: number;
}

// Auth Types
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData extends LoginCredentials {
  name: string;
  confirmPassword: string;
}
