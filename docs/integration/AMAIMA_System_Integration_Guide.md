# AMAIMA System Integration Guide

## Seamless Connection Architecture: Backend ↔ Frontend ↔ Mobile

---

## Table of Contents

1. [Integration Architecture](#1-integration-architecture)
2. [Authentication Integration](#2-authentication-integration)
3. [Real-Time Communication](#3-real-time-communication)
4. [Data Synchronization & Offline Support](#4-data-synchronization--offline-support)
5. [File Upload & Media Handling](#5-file-upload--media-handling)
6. [Error Handling Patterns](#6-error-handling-patterns)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Testing Integration](#8-testing-integration)
9. [Monitoring & Observability](#9-monitoring--observability)
10. [Complete Integration Examples](#10-complete-integration-examples)

---

## 1. Integration Architecture

### Unified Communication Layer

The AMAIMA system implements a **single unified API** that serves all three client platforms (Web, iOS, Android). This approach eliminates code duplication, ensures feature parity, and simplifies maintenance. The communication layer supports both synchronous REST calls for standard operations and asynchronous WebSocket connections for real-time streaming and updates.

The architecture follows a hub-and-spoke model where all clients connect to the API Gateway (NGINX), which load-balances requests across multiple backend instances. This design provides horizontal scalability, fault tolerance, and enables zero-downtime deployments. The gateway also handles cross-cutting concerns like rate limiting, SSL termination, and request logging, keeping the backend services focused on business logic.

All three platforms share the same authentication mechanism, real-time communication protocol, and error response format. This uniformity means that a feature implemented in the backend is immediately available to all clients without platform-specific adjustments. The frontend (Next.js) and mobile clients (Android/Kotlin) consume identical APIs, ensuring that users have a consistent experience regardless of their device.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Internet / CDN                                  │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      API Gateway (NGINX/Traefik)                         │
│                    Port: 443 (HTTPS/WSS)                                 │
│                                                                          │
│    ┌──────────────────────────────────────────────────────────────┐     │
│    │  • SSL Termination        • Rate Limiting (100 req/s)        │     │
│    │  • Load Balancing         • Request Routing                  │     │
│    │  • WebSocket Proxying     • CORS Headers                     │     │
│    │  • Health Checks          • Request Logging                  │     │
│    └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Web Frontend   │ │   Mobile Client  │ │   Backend API    │
│   Next.js 15     │ │   (Android APK)  │ │   FastAPI        │
│   Port: 3000     │ │   HTTP/JSON      │ │   Port: 8000     │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         │        HTTPS + JWT + WebSocket          │
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   PostgreSQL     │ │     Redis        │ │      S3          │
│   User Data      │ │     Cache        │ │   File Storage   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

### Communication Protocol Summary

The system uses four primary communication protocols to handle different use cases efficiently. HTTPS serves as the backbone for all REST API calls, providing secure, encrypted communication for authentication, data retrieval, and query submission. WebSocket Secure (WSS) enables bidirectional, real-time communication for streaming query responses, workflow execution updates, and system notifications. HTTP/2 is leveraged for frontend asset delivery, providing multiplexing and server push capabilities that improve page load times.

| Protocol | Use Case | Data Format | Security |
|----------|----------|-------------|----------|
| **HTTPS** | REST API calls (auth, queries, files) | JSON | TLS 1.3 + JWT |
| **WSS** | Real-time streaming, updates | JSON | TLS 1.3 + Token |
| **HTTP/2** | Frontend asset delivery | Binary/Brotli | TLS 1.3 |
| **gRPC** (internal) | Service-to-service RPC | Protocol Buffers | mTLS |

The API versioning strategy uses URL path prefixing (e.g., `/v1/query`, `/v1/auth`) which allows for backward-compatible evolution. Breaking changes are introduced through new version numbers rather than modifying existing endpoints. All clients should implement version checking and warn users when they're using an outdated client version.

---

## 2. Authentication Integration

### Unified Authentication Protocol

AMAIMA implements a unified JWT-based authentication system that serves all three platforms identically. The authentication flow follows the OAuth 2.0 specification with PKCE extension for mobile security, though the core token issuance and validation logic remains consistent across platforms. This approach ensures that authentication state, session management, and token refresh behave predictably regardless of how users access the system.

The authentication system issues two tokens: a short-lived access token (15 minutes) for API access, and a longer-lived refresh token (30 days) for obtaining new access tokens without re-authentication. The refresh token uses a unique identifier (JTI) that enables per-device logout and token blacklisting for security incident response. All tokens are signed using RS256 with RSA key pairs, and the public key is distributed to all services for validation.

Cross-platform authentication state synchronization is handled through a shared session token that ties the refresh token to the device. When users authenticate on a new device, they establish a fresh session. When they log out from any device, only that specific session terminates, allowing users to maintain multiple simultaneous sessions across different devices—a critical feature for productivity applications.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Authentication Flow                                 │
└─────────────────────────────────────────────────────────────────────────┘

Client                         API Gateway                    Backend
   │                               │                              │
   │  1. POST /v1/auth/login       │                              │
   │  {email, password}            │                              │
   │──────────────────────────────►│  Forward with Request-ID     │
   │                               │─────────────────────────────►│
   │                               │                              │ Validate
   │                               │                              │ credentials
   │                               │                              │ Generate
   │                               │                              │ tokens
   │  2. Response                  │                              │
   │  {access_token,               │◄─────────────────────────────│
   │   refresh_token, user}        │                              │
   │◄──────────────────────────────│                              │
   │                               │                              │
   │  3. API Request               │                              │
   │  Authorization: Bearer JWT    │                              │
   │──────────────────────────────►│  Validate JWT signature      │
   │                               │─────────────────────────────►│
   │                               │                              │ Verify
   │                               │                              │ claims
   │  4. Response                  │                              │
   │◄──────────────────────────────│◄─────────────────────────────│
   │                               │                              │
   │  5. Token refresh (when       │                              │
   │     access_token expires)     │                              │
   │  POST /v1/auth/refresh        │                              │
   │──────────────────────────────►│─────────────────────────────►│
   │                               │                              │ Validate
   │                               │                              │ refresh
   │                               │                              │ token
   │  6. New tokens response       │◄─────────────────────────────│
   │◄──────────────────────────────│                              │
```

### Token Structure and Validation

The JWT tokens follow a standardized structure that all platforms can parse and validate. The access token contains claims for the user identity (`sub`), token expiration (`exp`), issuance time (`iat`), and token type. The refresh token extends this with a unique identifier (`jti`) that enables blacklisting and a type claim distinguishing it from access tokens. All tokens include a request identifier that traces authentication events across the distributed system.

Backend validation extracts the user ID from the `sub` claim and fetches the complete user profile from the database on each authenticated request. This pattern ensures that user profile changes (permissions updates, account deletion) take effect immediately without waiting for token expiration. The validation layer also checks token blacklists maintained in Redis, enabling instant session termination when needed.

```python
# backend/auth/token_validation.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
from redis import Redis

# JWT configuration
ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Redis for token blacklisting
redis_client = Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

async def validate_token(token: str, expected_type: str = "access") -> dict:
    """
    Validate JWT token and return payload.
    
    This function performs the following checks:
    1. Verify token signature using RS256
    2. Check token type claim
    3. Verify token hasn't expired
    4. Check token blacklist
    5. Extract and return claims
    """
    
    try:
        # Decode token (verification happens automatically with complete=True)
        payload = jwt.decode(
            token,
            key=await get_public_key(),
            algorithms=[ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["sub", "exp", "iat", "type"]
            }
        )
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}, got {token_type}"
            )
        
        # Check blacklist for refresh tokens
        if token_type == "refresh":
            jti = payload.get("jti")
            if redis_client.sismember("blacklisted_tokens", jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
        
        # Verify user still exists and is active
        user = await get_user_by_id(payload.get("sub"))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> User:
    """
    Dependency for protected endpoints.
    Returns the authenticated user object.
    """
    
    payload = await validate_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user
```

### Platform-Specific Authentication Implementation

Each platform implements authentication through a consistent pattern: obtain credentials, exchange for tokens, store tokens securely, and attach tokens to subsequent requests. The frontend uses secure HTTP-only cookies for browser storage and the Web Crypto API for encryption. Mobile platforms use hardware-backed Keystore (Android) and Keychain (iOS) for secure storage. All platforms implement automatic token refresh before expiration to maintain seamless user experience.

```typescript
// frontend/lib/auth/auth-provider.tsx

'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { secureStorage } from '@/lib/utils/secure-storage';
import { apiClient } from '@/lib/api/client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Initialize authentication state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  async function initializeAuth() {
    try {
      const accessToken = secureStorage.getItem('access_token');
      const refreshToken = secureStorage.getItem('refresh_token');

      if (!accessToken || !refreshToken) {
        setIsLoading(false);
        return;
      }

      // Check if access token is expired or about to expire
      const tokenData = parseJwt(accessToken);
      const isExpired = Date.now() >= tokenData.exp * 1000;
      const needsRefresh = Date.now() >= (tokenData.exp - 300) * 1000; // 5 min buffer

      if (needsRefresh) {
        const success = await refreshAccessToken();
        if (!success) {
          await logout();
          setIsLoading(false);
          return;
        }
      }

      // Fetch user profile
      const response = await apiClient.get('/v1/auth/me');
      setUser(response.user);
    } catch (error) {
      console.error('Auth initialization failed:', error);
      await logout();
    } finally {
      setIsLoading(false);
    }
  }

  async function login(email: string, password: string) {
    const response = await apiClient.post('/v1/auth/login', { email, password });

    secureStorage.setItem('access_token', response.access_token);
    secureStorage.setItem('refresh_token', response.refresh_token);

    apiClient.setAuthToken(response.access_token);
    setUser(response.user);

    router.push('/dashboard');
  }

  async function logout() {
    try {
      const refreshToken = secureStorage.getItem('refresh_token');
      if (refreshToken) {
        await apiClient.post('/v1/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      secureStorage.removeItem('access_token');
      secureStorage.removeItem('refresh_token');
      apiClient.clearAuthToken();
      setUser(null);
      router.push('/login');
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    try {
      const refreshToken = secureStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await apiClient.post('/v1/auth/refresh', {
        refresh_token: refreshToken
      });

      secureStorage.setItem('access_token', response.access_token);
      secureStorage.setItem('refresh_token', response.refresh_token);

      apiClient.setAuthToken(response.access_token);
      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshToken: refreshAccessToken
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

function parseJwt(token: string): { exp: number; sub: string } {
  const base64Url = token.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(
    atob(base64)
      .split('')
      .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
      .join('')
  );
  return JSON.parse(jsonPayload);
}
```

```kotlin
// android/data/repository/AuthRepository.kt

interface AuthRepository {
    val authState: StateFlow<AuthState>
    
    suspend fun login(email: String, password: String): Result<User>
    suspend fun register(name: String, email: String, password: String): Result<User>
    suspend fun logout(): Result<Unit>
    suspend fun refreshToken(): Result<String>
    suspend fun getCurrentUser(): Result<User>
    suspend fun isAuthenticated(): Boolean
}

class AuthRepositoryImpl(
    private val api: AmaimaApi,
    private val encryptedPrefs: EncryptedPreferences,
    private val userDao: UserDao
) : AuthRepository {

    private val _authState = MutableStateFlow<AuthState>(AuthState.Loading)
    override val authState: StateFlow<AuthState> = _authState.asStateFlow()

    init {
        CoroutineScope(Dispatchers.IO).launch {
            initializeAuth()
        }
    }

    private suspend fun initializeAuth() {
        val accessToken = encryptedPrefs.getAccessToken()
        val refreshToken = encryptedPrefs.getRefreshToken()

        if (accessToken == null || refreshToken == null) {
            _authState.value = AuthState.Unauthenticated
            return
        }

        try {
            // Check token expiration
            if (isTokenExpired(accessToken)) {
                val refreshSuccess = refreshToken() == null
                if (!refreshSuccess) {
                    _authState.value = AuthState.Unauthenticated
                    return
                }
            }

            // Verify with backend
            val response = api.getCurrentUser()
            if (response.isSuccessful) {
                response.body()?.let { userDto ->
                    val user = userDto.toDomain()
                    userDao.insertUser(user.toEntity())
                    _authState.value = AuthState.Authenticated(user)
                }
            } else {
                clearAuthData()
                _authState.value = AuthState.Unauthenticated
            }
        } catch (e: Exception) {
            Log.e(TAG, "Auth initialization failed", e)
            clearAuthData()
            _authState.value = AuthState.Unauthenticated
        }
    }

    override suspend fun login(email: String, password: String): Result<User> {
        return withContext(Dispatchers.IO) {
            try {
                _authState.value = AuthState.Loading

                val response = api.login(LoginRequestDto(email, password))

                if (response.isSuccessful && response.body() != null) {
                    val loginResponse = response.body()!!

                    // Store tokens securely
                    encryptedPrefs.saveAccessToken(loginResponse.accessToken)
                    encryptedPrefs.saveRefreshToken(loginResponse.refreshToken)
                    encryptedPrefs.saveUserId(loginResponse.user.id)

                    // Store user in local database
                    val user = loginResponse.user.toDomain()
                    userDao.insertUser(user.toEntity())

                    _authState.value = AuthState.Authenticated(user)

                    Result.success(user)
                } else {
                    val errorMsg = response.body()?.error?.message ?: "Login failed"
                    _authState.value = AuthState.Error(errorMsg)
                    Result.failure(Exception(errorMsg))
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Unknown error")
                Result.failure(e)
            }
        }
    }

    override suspend fun logout(): Result<Unit> {
        return withContext(Dispatchers.IO) {
            try {
                val refreshToken = encryptedPrefs.getRefreshToken()

                // Notify server of logout (to blacklist refresh token)
                if (refreshToken != null) {
                    api.logout(LogoutRequestDto(refreshToken))
                }

                // Clear all local data
                clearAuthData()
                userDao.deleteAllUsers()

                _authState.value = AuthState.Unauthenticated

                Result.success(Unit)
            } catch (e: Exception) {
                // Still clear local data even if server call fails
                clearAuthData()
                userDao.deleteAllUsers()
                _authState.value = AuthState.Unauthenticated

                Result.success(Unit) // Consider this a success
            }
        }
    }

    override suspend fun refreshToken(): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val refreshToken = encryptedPrefs.getRefreshToken()
                    ?: return@withContext Result.failure(Exception("No refresh token"))

                val response = api.refreshToken(RefreshTokenRequestDto(refreshToken))

                if (response.isSuccessful && response.body() != null) {
                    val tokenResponse = response.body()!!

                    encryptedPrefs.saveAccessToken(tokenResponse.accessToken)
                    encryptedPrefs.saveRefreshToken(tokenResponse.refreshToken)

                    Result.success(tokenResponse.accessToken)
                } else {
                    // Refresh failed - user needs to re-authenticate
                    logout()
                    Result.failure(Exception("Token refresh failed"))
                }
            } catch (e: Exception) {
                logout()
                Result.failure(e)
            }
        }
    }

    private fun clearAuthData() {
        encryptedPrefs.clearAuthData()
    }

    private fun isTokenExpired(token: String): Boolean {
        return try {
            val claims = decodeJwt(token)
            val exp = claims["exp"] as Number
            System.currentTimeMillis() / 1000 >= exp.toLong()
        } catch (e: Exception) {
            true
        }
    }

    private fun decodeJwt(token: String): Map<String, Any> {
        val parts = token.split(".")
        val payload = parts[1]
        val decoded = Base64.getUrlDecoder().decode(payload)
        val json = String(decoded, Charset.forName("UTF-8"))
        return Gson().fromJson(json, object : TypeToken<Map<String, Any>>() {}.type)
    }

    companion object {
        private const val TAG = "AuthRepository"
    }
}

sealed class AuthState {
    object Loading : AuthState()
    object Unauthenticated : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data class Error(val message: String) : AuthState()
}
```

---

## 3. Real-Time Communication

### WebSocket Protocol Specification

The WebSocket layer provides real-time bidirectional communication for streaming query responses, workflow execution updates, and system notifications. All platforms share the same message protocol, enabling consistent behavior across web and mobile clients. The protocol supports subscription-based updates where clients can subscribe to specific resources (queries, workflows, system status) and receive push notifications when those resources change.

Connection management handles automatic reconnection with exponential backoff, preventing connection storms during network outages. Each connection is authenticated using the JWT access token passed as a query parameter during connection establishment. The server validates the token before accepting the WebSocket connection and closes the connection with appropriate codes for authentication failures.

Heartbeat mechanism maintains connection health through periodic ping-pong messages. The server sends ping messages every 30 seconds, and clients must respond with pong messages within 10 seconds. Connections that miss multiple heartbeats are considered dead and cleaned up server-side. This mechanism also serves as a network quality indicator, allowing clients to detect degraded connectivity before complete disconnection.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       WebSocket Message Protocol                         │
└─────────────────────────────────────────────────────────────────────────┘

CONNECTION ESTABLISHMENT:
┌─────────────────────────────────────────────────────────────────────┐
│ Client → Server: ws://api.amaima.com/v1/ws/query?token=<JWT>        │
│ Server → Client: {                                                  │
│   "type": "connection_established",                                 │
│   "data": {"userId": "uuid"},                                       │
│   "timestamp": "2024-01-15T10:30:00.000Z"                           │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘

QUERY SUBMISSION & STREAMING:
┌─────────────────────────────────────────────────────────────────────┐
│ Client → Server: {                                                  │
│   "type": "submit_query",                                           │
│   "query": "Explain quantum computing",                             │
│   "operation": "general"                                            │
│ }                                                                   │
│                                                                     │
│ Server → Client (multiple chunks):                                  │
│ { "type": "query_update", "data": { "chunk": "Quantum", ... } }     │
│ { "type": "query_update", "data": { "chunk": " computing is", ... } }│
│ { "type": "query_update", "data": { "chunk": " based on", ... } }   │
│ { "type": "query_update", "data": {                                 │
│   "complete": true,                                                 │
│   "responseText": "Quantum computing is based on...",               │
│   "verification": {"confidence": 0.95}                              │
│ }}                                                                   │
└─────────────────────────────────────────────────────────────────────┘

SUBSCRIPTION MANAGEMENT:
┌─────────────────────────────────────────────────────────────────────┐
│ Subscribe:     { "type": "subscribe_query", "queryId": "uuid" }     │
│ Confirmation:  { "type": "subscription_confirmed",                  │
│                 "data": {"queryId": "uuid"} }                       │
│ Unsubscribe:   { "type": "unsubscribe_query", "queryId": "uuid" }   │
└─────────────────────────────────────────────────────────────────────┘

HEARTBEAT:
┌─────────────────────────────────────────────────────────────────────┐
│ Server → Client: { "type": "ping", "timestamp": "..." }             │
│ Client → Server: { "type": "pong", "timestamp": "..." }             │
└─────────────────────────────────────────────────────────────────────┘
```

### Unified WebSocket Implementation

```typescript
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
  data: Record<string, unknown>;
  timestamp: string;
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
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      console.error('Max reconnect attempts reached');
      this.emit('reconnect_failed');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectBaseDelay! * Math.pow(2, this.reconnectAttempts - 1);
    
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

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // Queue message for when connection is restored
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
```

```kotlin
// android/data/websocket/WebSocketManager.kt

class WebSocketManager(
    private val okHttpClient: OkHttpClient,
    private val encryptedPrefs: EncryptedPreferences
) {
    private var webSocket: WebSocket? = null
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    private val baseReconnectDelay = 1000L
    private var isManualDisconnect = false
    private var heartbeatJob: Job? = null

    private val _messageFlow = MutableSharedFlow<WebSocketMessage>(
        replay = 0,
        extraBufferCapacity = 64
    )
    val messageFlow: SharedFlow<WebSocketMessage> = _messageFlow.asSharedFlow()

    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    sealed class ConnectionState {
        object CONNECTING : ConnectionState()
        object CONNECTED : ConnectionState()
        object DISCONNECTED : ConnectionState()
        data class ERROR(val message: String) : ConnectionState()
    }

    sealed class WebSocketMessage {
        data class QueryUpdate(val data: QueryUpdateData) : WebSocketMessage()
        data class WorkflowUpdate(val data: WorkflowUpdateData) : WebSocketMessage()
        data class SystemStatus(val data: SystemStatusData) : WebSocketMessage()
        data class ConnectionEstablished(val userId: String) : WebSocketMessage()
        data class SubscriptionConfirmed(val queryId: String) : WebSocketMessage()
        data class Error(val message: String) : WebSocketMessage()
        object Heartbeat : WebSocketMessage()
        object Ping : WebSocketMessage()
    }

    fun connect() {
        if (webSocket != null) {
            Log.d(TAG, "WebSocket already connected")
            return
        }

        val token = encryptedPrefs.getAccessToken()
        if (token == null) {
            Log.e(TAG, "No auth token available")
            _connectionState.value = ConnectionState.ERROR("No authentication token")
            return
        }

        isManualDisconnect = false
        _connectionState.value = ConnectionState.CONNECTING

        val request = Request.Builder()
            .url("${BuildConfig.WS_BASE_URL}/v1/ws/query?token=$token")
            .build()

        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket opened")
                reconnectAttempts = 0
                _connectionState.value = ConnectionState.CONNECTED
                startHeartbeat(webSocket)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closing: $code $reason")
                stopHeartbeat()
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closed: $code $reason")
                this@WebSocketManager.webSocket = null
                stopHeartbeat()
                _connectionState.value = ConnectionState.DISCONNECTED

                if (!isManualDisconnect && reconnectAttempts < maxReconnectAttempts) {
                    scheduleReconnect()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket error", t)
                this@WebSocketManager.webSocket = null
                stopHeartbeat()
                _connectionState.value = ConnectionState.ERROR(t.message ?: "Connection failed")

                if (!isManualDisconnect && reconnectAttempts < maxReconnectAttempts) {
                    scheduleReconnect()
                }
            }
        }

        webSocket = okHttpClient.newWebSocket(request, listener)
    }

    private fun startHeartbeat(webSocket: WebSocket) {
        heartbeatJob = CoroutineScope(Dispatchers.IO).launch {
            while (isActive) {
                delay(30000) // 30 seconds
                webSocket.send(
                    Json.encodeToString(
                        WebSocketMessage.serializer(),
                        WebSocketMessage.Heartbeat
                    )
                )
            }
        }
    }

    private fun stopHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = null
    }

    private fun scheduleReconnect() {
        reconnectAttempts++
        val delay = baseReconnectDelay * (2.0.pow(reconnectAttempts - 1)).toLong()
        
        Log.d(TAG, "Scheduling reconnect in ${delay}ms (attempt $reconnectAttempts)")
        
        CoroutineScope(Dispatchers.IO).launch {
            delay(delay)
            if (!isManualDisconnect) {
                connect()
            }
        }
    }

    private fun handleMessage(text: String) {
        try {
            val json = Json.parseToJsonElement(text).jsonObject
            val type = json["type"]?.jsonPrimitive?.contentOrNull ?: return

            CoroutineScope(Dispatchers.IO).launch {
                when (type) {
                    "connection_established" -> {
                        val userId = json["data"]?.jsonObject?.get("userId")?.jsonPrimitive?.content ?: ""
                        _messageFlow.emit(WebSocketMessage.ConnectionEstablished(userId))
                    }
                    
                    "query_update" -> {
                        val data = Json.decodeFromJsonElement<QueryUpdateData>(
                            json["data"]?.jsonObject ?: return@launch
                        )
                        _messageFlow.emit(WebSocketMessage.QueryUpdate(data))
                    }
                    
                    "workflow_update" -> {
                        val data = Json.decodeFromJsonElement<WorkflowUpdateData>(
                            json["data"]?.jsonObject ?: return@launch
                        )
                        _messageFlow.emit(WebSocketMessage.WorkflowUpdate(data))
                    }
                    
                    "subscription_confirmed" -> {
                        val queryId = json["data"]?.jsonObject?.get("queryId")?.jsonPrimitive?.content ?: ""
                        _messageFlow.emit(WebSocketMessage.SubscriptionConfirmed(queryId))
                    }
                    
                    "heartbeat" -> _messageFlow.emit(WebSocketMessage.Heartbeat)
                    
                    "ping" -> {
                        _messageFlow.emit(WebSocketMessage.Ping)
                        sendPong()
                    }
                    
                    "error" -> {
                        val message = json["data"]?.jsonObject?.get("message")?.jsonPrimitive?.content ?: "Unknown error"
                        _messageFlow.emit(WebSocketMessage.Error(message))
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse WebSocket message", e)
        }
    }

    fun sendMessage(message: Any) {
        val json = Json.encodeToString(message)
        webSocket?.send(json) ?: Log.w(TAG, "Cannot send message, WebSocket not connected")
    }

    fun subscribeToQuery(queryId: String) {
        sendMessage(mapOf(
            "type" to "subscribe_query",
            "queryId" to queryId,
            "timestamp" to Instant.now().toString()
        ))
    }

    fun submitQuery(query: String, operation: String = "general") {
        sendMessage(mapOf(
            "type" to "submit_query",
            "query" to query,
            "operation" to operation,
            "timestamp" to Instant.now().toString()
        ))
    }

    private fun sendPong() {
        sendMessage(mapOf(
            "type" to "pong",
            "timestamp" to Instant.now().toString()
        ))
    }

    fun disconnect() {
        isManualDisconnect = true
        reconnectAttempts = maxReconnectAttempts + 1
        stopHeartbeat()
        webSocket?.close(1000, "Client disconnect")
        webSocket = null
        _connectionState.value = ConnectionState.DISCONNECTED
    }

    companion object {
        private const val TAG = "WebSocketManager"
    }
}

@Serializable
data class QueryUpdateData(
    val queryId: String,
    val status: String? = null,
    val chunk: String? = null,
    val complete: Boolean? = null,
    val responseText: String? = null,
    val verification: VerificationData? = null
)

@Serializable
data class WorkflowUpdateData(
    val workflowId: String,
    val stepId: String,
    val status: String,
    val progress: Int? = null,
    val result: String? = null,
    val error: String? = null
)
```

---

## 4. Data Synchronization & Offline Support

### Offline-First Architecture

The AMAIMA system implements an offline-first architecture that allows users to continue working even when network connectivity is unavailable. This approach is particularly important for mobile users who may experience intermittent connectivity. The synchronization strategy uses local storage as the source of truth, with background synchronization reconciling local changes with the server when connectivity is restored.

The synchronization layer maintains a queue of pending operations (queries, workflow executions, file uploads) when offline. When connectivity returns, the queue is processed in order, with automatic retry using exponential backoff for failed operations. The conflict resolution strategy follows a "last-write-wins" pattern for most operations, with server-side validation rejecting conflicting changes.

Query results are cached locally with a configurable TTL (time-to-live). When users submit queries while offline, the system provides a queued confirmation and executes the query automatically when connectivity returns. For read operations, the cache serves stale data when offline, with a background refresh after reconnection. This ensures users always have access to their data regardless of network status.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Offline-First Synchronization Flow                    │
└─────────────────────────────────────────────────────────────────────────┘

ONLINE STATE:
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   User Action → Local Cache → API Request → Server Processing           │
│        ↓                  ↓              ↓              ↓                 │
│   Immediate write    Update immediately  Async request   Persistent      │
│   acknowledgment     in IndexedDB       Wait for       storage           │
│                                           response                       │
│                                                                          │
│   Real-time sync: All changes pushed immediately                        │
│   Cache strategy: Cache-aside with TTL-based invalidation               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

OFFLINE STATE:
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   User Action → Local Cache → Operation Queue                            │
│        ↓                  ↓              ↓                               │
│   Immediate write    Update immediately  Store for later                 │
│   acknowledgment     in IndexedDB       Batch process                    │
│                                           when online                    │
│                                                                          │
│   Conflict detection: Timestamp-based with last-write-wins               │
│   Retry strategy: Exponential backoff with jitter                        │
│   Notification: Toast notification when sync completes                   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

RECONNECTION:
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   Network Available → Process Queue → Batch Upload → Resolve Conflicts   │
│          ↓                   ↓              ↓              ↓              │
│   Detect via         Execute pending   Group by    Server validates      │
│   navigator.onLine   operations in     type for    and returns errors   │
│                      order             efficiency                       │
│                                                                          │
│   Success: Update local state, show notification                         │
│   Failure: Re-queue with backoff, alert user of persistent failures      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Synchronization Implementation

```typescript
// frontend/lib/sync/sync-manager.ts

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { queryClient } from '@/lib/query/client';

interface PendingOperation {
  id: string;
  type: 'query' | 'workflow' | 'file_upload' | 'settings';
  payload: Record<string, unknown>;
  timestamp: number;
  retryCount: number;
}

interface SyncDBSchema extends DBSchema {
  pendingOperations: {
    key: string;
    value: PendingOperation;
    indexes: { 'by-timestamp': number; 'by-type': string };
  };
  cache: {
    key: string;
    value: { data: unknown; timestamp: number; ttl: number };
    indexes: { 'by-timestamp': number };
  };
  localState: {
    key: string;
    value: unknown;
  };
}

class SyncManager {
  private db: IDBPDatabase<SyncDBSchema> | null = null;
  private syncInterval: NodeJS.Timeout | null = null;
  private readonly SYNC_INTERVAL_MS = 5 * 60 * 1000;
  private readonly MAX_RETRY_COUNT = 3;

  async initialize(): Promise<void> {
    this.db = await openDB<SyncDBSchema>('amaima-sync', 1, {
      upgrade(db) {
        // Pending operations store
        db.createObjectStore('pendingOperations', { keyPath: 'id' });
        db.createObjectStore('pendingOperations').createIndex('by-timestamp', 'timestamp');
        db.createObjectStore('pendingOperations').createIndex('by-type', 'type');

        // Cache store
        db.createObjectStore('cache', { keyPath: 'key' });
        db.createObjectStore('cache').createIndex('by-timestamp', 'timestamp');

        // Local state store
        db.createObjectStore('localState', { keyPath: 'key' });
      },
    });

    // Start periodic sync
    this.startPeriodicSync();

    // Listen for network events
    window.addEventListener('online', this.handleOnline);
    window.addEventListener('offline', this.handleOffline);
    document.addEventListener('visibilitychange', this.handleVisibilityChange);

    // Initial sync if online
    if (navigator.onLine) {
      this.sync();
    }
  }

  private startPeriodicSync(): void {
    this.syncInterval = setInterval(() => {
      if (navigator.onLine) {
        this.sync();
      }
    }, this.SYNC_INTERVAL_MS);
  }

  private handleOnline = (): void => {
    console.log('Network online - starting sync');
    this.sync();
  };

  private handleOffline = (): void => {
    console.log('Network offline - queuing operations locally');
  };

  private handleVisibilityChange = (): void => {
    if (document.visibilityState === 'visible' && navigator.onLine) {
      this.sync();
    }
  };

  async queueOperation(
    type: PendingOperation['type'],
    payload: Record<string, unknown>
  ): Promise<string> {
    if (!this.db) await this.initialize();

    const operation: PendingOperation = {
      id: `${type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      payload,
      timestamp: Date.now(),
      retryCount: 0,
    };

    await this.db!.put('pendingOperations', operation);
    console.log(`Queued ${type} operation: ${operation.id}`);

    // If online, trigger immediate sync
    if (navigator.onLine) {
      this.sync();
    }

    return operation.id;
  }

  async sync(): Promise<void> {
    if (!this.db) await this.initialize();

    const pendingOps = await this.db!.getAllFromIndex(
      'pendingOperations',
      'by-timestamp'
    );

    if (pendingOps.length === 0) {
      console.log('No pending operations to sync');
      return;
    }

    console.log(`Syncing ${pendingOps.length} pending operations`);

    for (const operation of pendingOps) {
      try {
        await this.processOperation(operation);
        await this.db!.delete('pendingOperations', operation.id);
        console.log(`Synced operation: ${operation.id}`);
      } catch (error) {
        console.error(`Failed to sync operation ${operation.id}:`, error);

        if (operation.retryCount < this.MAX_RETRY_COUNT) {
          await this.db!.put('pendingOperations', {
            ...operation,
            retryCount: operation.retryCount + 1,
          });
        } else {
          // Max retries exceeded - notify user
          await this.notifySyncFailure(operation, error);
          await this.db!.delete('pendingOperations', operation.id);
        }
      }
    }

    // Refresh cached data after sync
    await this.refreshCache();
  }

  private async processOperation(operation: PendingOperation): Promise<void> {
    const accessToken = await this.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    };

    switch (operation.type) {
      case 'query':
        await this.syncQuery(operation.payload);
        break;
      case 'workflow':
        await this.syncWorkflow(operation.payload);
        break;
      case 'file_upload':
        await this.syncFileUpload(operation.payload);
        break;
      case 'settings':
        await this.syncSettings(operation.payload);
        break;
    }
  }

  private async syncQuery(payload: Record<string, unknown>): Promise<void> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/query`, {
      method: 'POST',
      headers: { ...await this.getAuthHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Query sync failed: ${response.status}`);
    }

    const result = await response.json();

    // Update local cache
    await this.cacheData(`query_${payload.queryId}`, result, 5 * 60 * 1000);

    // Invalidate React Query cache
    queryClient.invalidateQueries({ queryKey: ['queries'] });
  }

  private async syncWorkflow(payload: Record<string, unknown>): Promise<void> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/workflow`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Workflow sync failed: ${response.status}`);
    }
  }

  private async syncFileUpload(payload: Record<string, unknown>): Promise<void> {
    const formData = new FormData();
    formData.append('file', payload.file as File);

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/files/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${await this.getAccessToken()}`,
      },
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`File upload sync failed: ${response.status}`);
    }
  }

  private async syncSettings(payload: Record<string, unknown>): Promise<void> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/settings`, {
      method: 'PUT',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Settings sync failed: ${response.status}`);
    }
  }

  async cacheData(key: string, data: unknown, ttl: number): Promise<void> {
    if (!this.db) await this.initialize();

    await this.db!.put('cache', {
      key,
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  async getCachedData<T>(key: string): Promise<T | null> {
    if (!this.db) await this.initialize();

    const cached = await this.db!.get('cache', key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > cached.ttl) {
      await this.db!.delete('cache', key);
      return null;
    }

    return cached.data as T;
  }

  private async refreshCache(): Promise<void> {
    // Refresh recent queries
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/queries?limit=20`,
        { headers: await this.getAuthHeaders() }
      );

      if (response.ok) {
        const queries = await response.json();
        await this.cacheData('recent_queries', queries, 5 * 60 * 1000);
        queryClient.setQueryData(['queries'], queries);
      }
    } catch (error) {
      console.error('Failed to refresh cache:', error);
    }
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await this.getAccessToken();
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  }

  private async getAccessToken(): Promise<string | null> {
    return secureStorage.getItem('access_token');
  }

  private async notifySyncFailure(
    operation: PendingOperation,
    error: unknown
  ): Promise<void> {
    // Could integrate with toast notification system
    console.error(`Persistent sync failure for ${operation.type}:`, error);
  }

  async getPendingOperationCount(): Promise<number> {
    if (!this.db) await this.initialize();
    return this.db!.count('pendingOperations');
  }

  async clearAllData(): Promise<void> {
    if (!this.db) await this.initialize();

    await this.db!.clear('pendingOperations');
    await this.db!.clear('cache');
    await this.db!.clear('localState');

    queryClient.clear();
  }

  destroy(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    window.removeEventListener('online', this.handleOnline);
    window.removeEventListener('offline', this.handleOffline);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
  }
}

export const syncManager = new SyncManager();
```

```kotlin
// android/data/sync/SyncWorker.kt

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val queryDao: QueryDao,
    private val workflowDao: WorkflowDao,
    private val fileDao: FileDao,
    private val api: AmaimaApi,
    private val networkMonitor: NetworkMonitor,
    private val preferences: UserPreferences
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        if (!networkMonitor.isOnline()) {
            Log.d(TAG, "No network, deferring sync")
            return Result.retry()
        }

        Log.d(TAG, "Starting background sync")

        return try {
            // Sync pending queries
            val queriesSynced = syncPendingQueries()
            Log.d(TAG, "Synced $queriesSynced queries")

            // Sync pending workflows
            val workflowsSynced = syncPendingWorkflows()
            Log.d(TAG, "Synced $workflowsSynced workflows")

            // Sync pending file uploads
            val filesSynced = syncPendingFileUploads()
            Log.d(TAG, "Synced $filesSynced files")

            // Sync settings
            syncSettings()

            // Fetch latest data
            fetchLatestData()

            // Update last sync timestamp
            preferences.updateLastSyncTime(System.currentTimeMillis())

            Result.success()
        } catch (e: Exception) {
            Log.e(TAG, "Sync failed", e)
            
            if (runAttemptCount < 3) {
                Result.retry()
            } else {
                Result.failure()
            }
        }
    }

    private suspend fun syncPendingQueries(): Int {
        val pendingQueries = queryDao.getPendingQueries()
        var successCount = 0

        for (query in pendingQueries) {
            try {
                val response = api.submitQuery(QueryRequestDto(
                    query = query.queryText,
                    operation = query.operation,
                    metadata = query.metadata
                ))

                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!
                    
                    // Update local query with server response
                    queryDao.updateQuery(query.copy(
                        responseText = result.responseText,
                        modelUsed = result.modelUsed,
                        confidence = result.confidence,
                        latencyMs = result.latencyMs,
                        status = QueryStatus.COMPLETED.name,
                        syncStatus = SyncStatus.SYNCED,
                        serverQueryId = result.queryId
                    ))
                    
                    successCount++
                    
                    // Show notification
                    showSyncNotification("Query synced", query.queryText.take(50))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync query ${query.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncPendingWorkflows(): Int {
        val pendingWorkflows = workflowDao.getPendingWorkflows()
        var successCount = 0

        for (workflow in pendingWorkflows) {
            try {
                val response = api.createWorkflow(workflow.toDto())

                if (response.isSuccessful && response.body() != null) {
                    workflowDao.updateWorkflow(workflow.copy(
                        serverId = response.body()!!.workflowId,
                        syncStatus = SyncStatus.SYNCED
                    ))
                    successCount++
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync workflow ${workflow.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncPendingFileUploads(): Int {
        val pendingFiles = fileDao.getPendingUploads()
        var successCount = 0

        for (file in pendingFiles) {
            try {
                val fileEntity = File(file.localPath)
                val requestBody = fileEntity.asRequestBody("application/octet-stream".toMediaTypeOrNull())
                val multipartBody = MultipartBody.Part.createFormData(
                    "file",
                    fileEntity.name,
                    requestBody
                )

                val response = api.uploadFile(multipartBody)

                if (response.isSuccessful && response.body() != null) {
                    fileDao.updateFile(file.copy(
                        serverId = response.body()!!.fileId,
                        url = response.body()!!.url,
                        syncStatus = SyncStatus.SYNCED
                    ))
                    successCount++
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to sync file ${file.localId}", e)
            }
        }

        return successCount
    }

    private suspend fun syncSettings() {
        try {
            val response = api.getSettings()
            if (response.isSuccessful && response.body() != null) {
                preferences.updateSettings(response.body()!!.toSettings())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to sync settings", e)
        }
    }

    private suspend fun fetchLatestData() {
        // Fetch recent queries
        try {
            val response = api.getQueries(limit = 20)
            if (response.isSuccessful && response.body() != null) {
                response.body()!!.forEach { dto ->
                    queryDao.insertQuery(dto.toEntity())
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch queries", e)
        }

        // Fetch active workflows
        try {
            val response = api.getWorkflows(status = "active")
            if (response.isSuccessful && response.body() != null) {
                response.body()!!.forEach { dto ->
                    workflowDao.insertWorkflow(dto.toEntity())
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to fetch workflows", e)
        }
    }

    private fun showSyncNotification(title: String, message: String) {
        val notificationManager = applicationContext.getSystemService(
            Context.NOTIFICATION_SERVICE
        ) as NotificationManager

        val notification = NotificationCompat.Builder(applicationContext, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(message)
            .setSmallIcon(R.drawable.ic_sync)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(NOTIFICATION_ID++, notification)
    }

    companion object {
        private const val TAG = "SyncWorker"
        private const val CHANNEL_ID = "amaima_sync"
        private var NOTIFICATION_ID = 1000

        fun schedule(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build()

            val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
                repeatInterval = 15,
                repeatIntervalTimeUnit = TimeUnit.MINUTES
            )
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    WorkRequest.MIN_BACKOFF_MILLIS,
                    TimeUnit.MILLISECONDS
                )
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                syncRequest
            )
        }
    }
}
```

---

## 5. File Upload & Media Handling

### Unified File Upload Protocol

The file upload system provides a consistent interface across all platforms for uploading, managing, and retrieving files. The backend implements server-side validation for file types, sizes, and content scanning, while clients handle local file selection and upload progress tracking. Files are stored in S3-compatible storage with presigned URLs for efficient retrieval.

The upload flow supports both single-file and multi-file uploads with progress tracking. Large files (over 10MB) can use chunked uploads for improved reliability, though the implementation is transparent to the API consumer. File metadata including checksums, MIME types, and scan results are stored in the database for validation and audit purposes.

File access is controlled through presigned URLs with configurable expiration times. The default expiration is 1 hour for regular access, with longer durations available for specific use cases. All file operations require authentication, and users can only access files they've uploaded or that have been explicitly shared with them.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       File Upload Flow                                   │
└─────────────────────────────────────────────────────────────────────────┘

1. CLIENT UPLOAD REQUEST
┌─────────────────────────────────────────────────────────────────────────┐
│ POST /v1/files/upload                                                   │
│ Content-Type: multipart/form-data                                       │
│ Authorization: Bearer <JWT>                                             │
│                                                                         │
│ Response (200 OK):                                                      │
│ {                                                                       │
│   "file_id": "userId_timestamp_checksum",                               │
│   "filename": "document.pdf",                                           │
│   "mime_type": "application/pdf",                                       │
│   "size": 1048576,                                                      │
│   "url": "https://s3.amazonaws.com/...",                                │
│   "checksum": "sha256:abc123...",                                       │
│   "upload_date": "2024-01-15T10:30:00Z"                                 │
│ }                                                                       │
└─────────────────────────────────────────────────────────────────────────┘

2. FILE RETRIEVAL
┌─────────────────────────────────────────────────────────────────────────┐
│ GET /v1/files/{file_id}                                                 │
│ Authorization: Bearer <JWT>                                             │
│                                                                         │
│ Response (200 OK):                                                      │
│ {                                                                       │
│   "file_id": "...",                                                     │
│   "filename": "...",                                                    │
│   "url": "https://s3.amazonaws.com/...?X-Amz-..." (presigned URL)      │
│ }                                                                       │
│                                                                         │
│ Browser可以直接下载或显示文件:                                          │
│ <img src={url} /> 或 <a href={url} download>Download</a>                │
└─────────────────────────────────────────────────────────────────────────┘

3. UPLOAD WITH QUERY
┌─────────────────────────────────────────────────────────────────────────┐
│ POST /v1/query                                                          │
│ {                                                                       │
│   "query": "Analyze this document",                                     │
│   "file_ids": ["file_id_1", "file_id_2"]                                │
│ }                                                                       │
│                                                                         │
│ Backend会下载并处理关联的文件，将内容附加到查询上下文中                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Cross-Platform File Upload Implementation

```typescript
// frontend/lib/upload/file-uploader.ts

import { secureStorage } from '@/lib/utils/secure-storage';

interface UploadProgress {
  fileId: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

interface FileMetadata {
  file_id: string;
  filename: string;
  mime_type: string;
  size: number;
  url: string;
  checksum: string;
  upload_date: string;
}

class FileUploader {
  private readonly API_URL: string;

  constructor() {
    this.API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async uploadFile(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<FileMetadata> {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress({
            fileId: 'pending',
            progress,
            status: 'uploading',
          });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const metadata: FileMetadata = JSON.parse(xhr.responseText);
          onProgress?.({
            fileId: metadata.file_id,
            progress: 100,
            status: 'completed',
          });
          resolve(metadata);
        } else {
          const error = JSON.parse(xhr.responseText);
          onProgress?.({
            fileId: 'pending',
            progress: 0,
            status: 'error',
            error: error.error?.message || 'Upload failed',
          });
          reject(new Error(error.error?.message || `Upload failed: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        const error = new Error('Network error during upload');
        onProgress?.({
          fileId: 'pending',
          progress: 0,
          status: 'error',
          error: error.message,
        });
        reject(error);
      });

      xhr.open('POST', `${this.API_URL}/v1/files/upload`);
      xhr.setRequestHeader(
        'Authorization',
        `Bearer ${secureStorage.getItem('access_token')}`
      );
      xhr.send(formData);
    });
  }

  async uploadMultipleFiles(
    files: File[],
    onProgress?: (progress: UploadProgress) => void
  ): Promise<FileMetadata[]> {
    const results: FileMetadata[] = [];
    const errors: Error[] = [];

    for (const file of files) {
      try {
        const result = await this.uploadFile(file, onProgress);
        results.push(result);
      } catch (error) {
        errors.push(error as Error);
      }
    }

    if (results.length === 0 && errors.length > 0) {
      throw errors[0];
    }

    return results;
  }

  async getPresignedUrl(fileId: string): Promise<string> {
    const response = await fetch(`${this.API_URL}/v1/files/${fileId}`, {
      headers: {
        Authorization: `Bearer ${secureStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get file URL');
    }

    const metadata: FileMetadata = await response.json();
    return metadata.url;
  }

  async deleteFile(fileId: string): Promise<void> {
    const response = await fetch(`${this.API_URL}/v1/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${secureStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete file');
    }
  }

  async downloadFile(fileId: string, filename?: string): Promise<void> {
    const url = await this.getPresignedUrl(fileId);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error('Failed to download file');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  validateFile(file: File, options: UploadValidationOptions): ValidationResult {
    const errors: string[] = [];

    // Check file size
    if (file.size > options.maxSize) {
      errors.push(
        `File too large. Maximum size is ${(options.maxSize / (1024 * 1024)).toFixed(0)}MB`
      );
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (options.allowedExtensions && !options.allowedExtensions.includes(extension)) {
      errors.push(
        `File type ${extension} not allowed. Allowed types: ${options.allowedExtensions.join(', ')}`
      );
    }

    // Check MIME type
    if (options.allowedMimeTypes && !options.allowedMimeTypes.includes(file.type)) {
      errors.push(`MIME type ${file.type} not allowed`);
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

interface UploadValidationOptions {
  maxSize?: number;
  allowedExtensions?: string[];
  allowedMimeTypes?: string[];
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export const fileUploader = new FileUploader();
```

```kotlin
// android/data/repository/FileRepository.kt

class FileRepositoryImpl(
    private val api: AmaimaApi,
    private val context: Context
) : FileRepository {

    override suspend fun uploadFile(
        file: File,
        onProgress: (Float) -> Unit
    ): Result<FileMetadata> {
        return withContext(Dispatchers.IO) {
            try {
                val requestBody = file.asRequestBody(
                    getMimeType(file.name).toMediaTypeOrNull()
                )

                val multipartBody = MultipartBody.Part.createFormData(
                    "file",
                    file.name,
                    ProgressRequestBody(requestBody) { percentage ->
                        CoroutineScope(Dispatchers.Main).launch {
                            onProgress(percentage)
                        }
                    }
                )

                val response = api.uploadFile(multipartBody)

                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!.toDomain())
                } else {
                    Result.failure(
                        Exception(
                            response.body()?.error?.message
                                ?: "Upload failed: ${response.code()}"
                        )
                    )
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    override suspend fun uploadMultipleFiles(
        files: List<File>,
        onProgress: (Int, Float) -> Unit
    ): Result<List<FileMetadata>> {
        return withContext(Dispatchers.IO) {
            val results = mutableListOf<FileMetadata>()
            var totalProgress = 0f

            files.forEachIndexed { index, file ->
                val fileProgress: suspend (Float) -> Unit = { progress ->
                    val overallProgress = (totalProgress + progress / files.size) / 100f
                    onProgress(index, overallProgress)
                }

                when (val result = uploadFile(file, fileProgress)) {
                    is Result.Success -> results.add(result.getOrNull()!!)
                    is Result.Failure -> {
                        Log.e(TAG, "Failed to upload ${file.name}", result.exceptionOrNull())
                    }
                }
                totalProgress += 100f / files.size
            }

            if (results.isNotEmpty()) {
                Result.success(results)
            } else {
                Result.failure(Exception("All uploads failed"))
            }
        }
    }

    override suspend fun getPresignedUrl(fileId: String): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.getFileMetadata(fileId)

                if (response.isSuccessful && response.body() != null) {
                    Result.success(response.body()!!.url)
                } else {
                    Result.failure(Exception("Failed to get file URL"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    override suspend fun downloadFile(
        fileId: String,
        destinationFile: File,
        onProgress: (Float) -> Unit
    ): Result<File> {
        return withContext(Dispatchers.IO) {
            try {
                // Get presigned URL
                val urlResult = getPresignedUrl(fileId)
                if (urlResult.isFailure) {
                    return@withContext Result.failure(urlResult.exceptionOrNull()!!)
                }

                val url = urlResult.getOrNull()!!

                // Download file
                val client = OkHttpClient()
                val request = Request.Builder().url(url).build()

                client.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) {
                        return@withContext Result.failure(Exception("Download failed"))
                    }

                    val body = response.body ?: return@withContext Result.failure(
                        Exception("Empty response body")
                    )

                    val totalBytes = body.contentLength()
                    var downloadedBytes = 0L

                    destinationFile.outputStream().use { output ->
                        body.byteStream().use { input ->
                            val buffer = ByteArray(8192)
                            var bytesRead: Int

                            while (input.read(buffer).also { bytesRead = it } != -1) {
                                output.write(buffer, 0, bytesRead)
                                downloadedBytes += bytesRead

                                if (totalBytes > 0) {
                                    val progress = (downloadedBytes * 100f / totalBytes)
                                    CoroutineScope(Dispatchers.Main).launch {
                                        onProgress(progress)
                                    }
                                }
                            }
                        }
                    }
                }

                Result.success(destinationFile)
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    override suspend fun deleteFile(fileId: String): Result<Unit> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.deleteFile(fileId)

                if (response.isSuccessful) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception("Delete failed: ${response.code()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    private fun getMimeType(filename: String): String {
        val extension = filename.substringAfterLast('.', "")
        return when (extension.lowercase()) {
            "pdf" -> "application/pdf"
            "png" -> "image/png"
            "jpg", "jpeg" -> "image/jpeg"
            "txt" -> "text/plain"
            "json" -> "application/json"
            "csv" -> "text/csv"
            "py", "js", "ts" -> "text/plain"
            else -> "application/octet-stream"
        }
    }

    companion object {
        private const val TAG = "FileRepository"
    }
}

// Progress request body for OkHttp
class ProgressRequestBody(
    private val requestBody: RequestBody,
    private val progressListener: (Float) -> Unit
) : RequestBody() {

    override fun contentType(): MediaType? = requestBody.contentType()

    override fun contentLength(): Long = requestBody.contentLength()

    override fun writeTo(sink: BufferedSink) {
        val countingSink = CountingSink(sink, contentLength())
        val bufferedSink = countingSink.buffer()
        requestBody.writeTo(bufferedSink)
        bufferedSink.flush()
    }

    private inner class CountingSink(
        sink: Sink,
        private val totalBytes: Long
    ) : ForwardingSink(sink) {
        private var bytesWritten = 0L

        override fun write(source: Buffer, byteCount: Long) {
            super.write(source, byteCount)
            bytesWritten += byteCount
            progressListener(bytesWritten * 100f / totalBytes)
        }
    }
}
```

---

## 6. Error Handling Patterns

### Unified Error Response Format

All API responses follow a consistent error format that enables clients to handle errors uniformly. The error structure includes an error code for programmatic handling, a human-readable message, optional details for validation errors, and metadata for debugging. This consistency allows clients to implement generic error handling that works across all endpoints.

The error handling strategy distinguishes between client errors (4xx) and server errors (5xx). Client errors typically require user action (validation, authentication), while server errors trigger automatic retry with exponential backoff. The backend also includes request tracing through a unique request ID that appears in all logs and error responses, enabling correlation of distributed traces.

Error codes are hierarchical, with prefix categories indicating the error type. `AUTH_*` codes relate to authentication and authorization, `VALIDATION_*` to input validation, `QUERY_*` to query processing, and `SYSTEM_*` to infrastructure issues. This hierarchy helps clients implement targeted error handling.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Standard Error Response                            │
└─────────────────────────────────────────────────────────────────────────┘

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "type": "validation_error",
    "details": [
      {
        "field": "query",
        "message": "Field is required",
        "type": "missing_field"
      }
    ]
  },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "path": "/v1/query"
  }
}

┌─────────────────────────────────────────────────────────────────────────┐
│                       Error Code Reference                               │
└─────────────────────────────────────────────────────────────────────────┘

AUTH_*: Authentication & Authorization
  - AUTH_TOKEN_EXPIRED: JWT token has expired
  - AUTH_TOKEN_INVALID: JWT signature or claims invalid
  - AUTH_PERMISSION_DENIED: User lacks required permissions
  - AUTH_USER_NOT_FOUND: Authenticated user doesn't exist

VALIDATION_*: Input Validation
  - VALIDATION_ERROR: General validation failure
  - VALIDATION_MISSING_FIELD: Required field absent
  - VALIDATION_INVALID_FORMAT: Field format incorrect
  - VALIDATION_TOO_LARGE: Payload exceeds size limit

QUERY_*: Query Processing
  - QUERY_PROCESSING_ERROR: Internal query processing failed
  - QUERY_TIMEOUT: Query exceeded time limit
  - QUERY_MODEL_ERROR: Model inference failed
  - QUERY_ROUTING_ERROR: Could not route query

SYSTEM_*: Infrastructure
  - SYSTEM_INTERNAL_ERROR: Unhandled server error
  - SYSTEM_UNAVAILABLE: Service temporarily unavailable
  - SYSTEM_RATE_LIMITED: Too many requests
  - SYSTEM_DATABASE_ERROR: Database operation failed
```

### Cross-Platform Error Handling

```typescript
// frontend/lib/api/error-handler.ts

interface ApiError {
  code: string;
  message: string;
  type: string;
  details?: ValidationErrorDetail[];
}

interface ValidationErrorDetail {
  field: string;
  message: string;
  type: string;
}

interface ErrorMeta {
  request_id: string;
  timestamp: string;
  path: string;
}

interface ErrorResponse {
  error: ApiError;
  meta: ErrorMeta;
}

export class ApiError extends Error {
  code: string;
  type: string;
  details?: ValidationErrorDetail[];
  requestId?: string;
  timestamp?: string;
  path?: string;

  constructor(response: ErrorResponse) {
    super(response.error.message);
    this.name = 'ApiError';
    this.code = response.error.code;
    this.type = response.error.type;
    this.details = response.error.details;
    this.requestId = response.meta.request_id;
    this.timestamp = response.meta.timestamp;
    this.path = response.meta.path;
  }

  static isApiError(error: unknown): error is ApiError {
    return (
      error instanceof ApiError ||
      (typeof error === 'object' &&
        error !== null &&
        'code' in error &&
        'message' in error &&
        'type' in error)
    );
  }

  static async fromResponse(response: Response): Promise<ApiError> {
    try {
      const errorResponse: ErrorResponse = await response.json();
      return new ApiError(errorResponse);
    } catch {
      // Fallback if response body isn't valid JSON
      return new ApiError({
        error: {
          code: `HTTP_${response.status}`,
          message: response.statusText || 'Unknown error',
          type: 'http_error',
        },
        meta: {
          request_id: '',
          timestamp: new Date().toISOString(),
          path: '',
        },
      });
    }
  }
}

export function createErrorHandler() {
  const errorHandlers: Map<string, (error: ApiError) => void> = new Map();

  // Register default error handlers
  errorHandlers.set('AUTH_TOKEN_EXPIRED', () => {
    // Trigger token refresh
    authStore.getState().refreshToken();
  });

  errorHandlers.set('AUTH_PERMISSION_DENIED', () => {
    // Redirect to unauthorized page or show permission error
    router.push('/unauthorized');
  });

  errorHandlers.set('VALIDATION_ERROR', (error) => {
    // Display validation errors in form fields
    error.details?.forEach((detail) => {
      const fieldElement = document.querySelector(`[name="${detail.field}"]`);
      if (fieldElement) {
        fieldElement.classList.add('error');
        fieldElement.setAttribute('data-error', detail.message);
      }
    });
  });

  errorHandlers.set('SYSTEM_RATE_LIMITED', (error) => {
    // Show rate limit notification
    toast.error('Too many requests. Please wait before trying again.');
  });

  errorHandlers.set('SYSTEM_UNAVAILABLE', () => {
    // Show service unavailable message
    toast.error('Service temporarily unavailable. Retrying...');
  });

  return {
    handle(error: unknown, context?: string): ApiError | null {
      let apiError: ApiError;

      if (ApiError.isApiError(error)) {
        apiError = error as ApiError;
      } else if (error instanceof Error && error.message) {
        // Convert generic errors
        apiError = new ApiError({
          error: {
            code: 'UNKNOWN_ERROR',
            message: error.message,
            type: 'unknown',
          },
          meta: {
            request_id: '',
            timestamp: new Date().toISOString(),
            path: context || '',
          },
        });
      } else {
        apiError = new ApiError({
          error: {
            code: 'UNKNOWN_ERROR',
            message: 'An unknown error occurred',
            type: 'unknown',
          },
          meta: {
            request_id: '',
            timestamp: new Date().toISOString(),
            path: context || '',
          },
        });
      }

      // Log error
      console.error('API Error:', {
        code: apiError.code,
        message: apiError.message,
        path: apiError.path,
        requestId: apiError.requestId,
      });

      // Call registered handler
      const handler = errorHandlers.get(apiError.code);
      if (handler) {
        handler(apiError);
      } else if (apiError.code.startsWith('SYSTEM_')) {
        // Default handler for system errors
        errorHandlers.get('SYSTEM_UNAVAILABLE')?.(apiError);
      }

      return apiError;
    },

    registerHandler(code: string, handler: (error: ApiError) => void) {
      errorHandlers.set(code, handler);
    },

    removeHandler(code: string) {
      errorHandlers.delete(code);
    },
  };
}
```

```kotlin
// android/data/exception/ApiException.kt

sealed class ApiException(
    message: String,
    val code: String,
    val details: List<ErrorDetail>? = null
) : Exception(message) {
    data class ErrorDetail(
        val field: String,
        val message: String,
        val type: String
    )

    // Authentication errors
    data class TokenExpired(override val message: String) : ApiException(
        message, "AUTH_TOKEN_EXPIRED"
    )

    data class Unauthorized(override val message: String) : ApiException(
        message, "AUTH_PERMISSION_DENIED"
    )

    // Validation errors
    data class ValidationFailed(
        override val details: List<ErrorDetail>,
        message: String = "Validation failed"
    ) : ApiException(message, "VALIDATION_ERROR", details)

    // System errors
    data class RateLimited(override val message: String) : ApiException(
        message, "SYSTEM_RATE_LIMITED"
    )

    data class ServiceUnavailable(override val message: String) : ApiException(
        message, "SYSTEM_UNAVAILABLE"
    )

    data class InternalError(override val message: String) : ApiException(
        message, "SYSTEM_INTERNAL_ERROR"
    )

    companion object {
        fun fromResponse(response: Response<*>): ApiException {
            val errorBody = response.errorBody()?.string() ?: return InternalError("Unknown error")

            return try {
                val json = Json.parseToJsonElement(errorBody).jsonObject
                val error = json["error"]?.jsonObject
                val meta = json["meta"]?.jsonObject

                val code = error?.get("code")?.jsonPrimitive?.content ?: "UNKNOWN"
                val message = error?.get("message")?.jsonPrimitive?.content ?: "Unknown error"
                val details = error?.get("details")?.jsonArray
                    ?.map { element ->
                        val detailObj = element.jsonObject
                        ErrorDetail(
                            field = detailObj["field"]?.jsonPrimitive?.content ?: "",
                            message = detailObj["message"]?.jsonPrimitive?.content ?: "",
                            type = detailObj["type"]?.jsonPrimitive?.content ?: ""
                        )
                    }

                when (code) {
                    "AUTH_TOKEN_EXPIRED" -> TokenExpired(message)
                    "AUTH_PERMISSION_DENIED" -> Unauthorized(message)
                    "VALIDATION_ERROR" -> ValidationFailed(details ?: emptyList(), message)
                    "SYSTEM_RATE_LIMITED" -> RateLimited(message)
                    "SYSTEM_UNAVAILABLE" -> ServiceUnavailable(message)
                    else -> InternalError(message)
                }
            } catch (e: Exception) {
                InternalError("Failed to parse error response")
            }
        }
    }
}

// Exception mapper for Retrofit
class ExceptionMapper<T> : Converter<ResponseBody, T> {
    override fun convert(value: ResponseBody): T? {
        val error = ApiException.fromResponse(
            Response.error<T>(500, value, Retrofit.Builder().baseUrl("").build())
        )
        throw error as? T ?: throw error
    }
}

// Global error handler
object GlobalErrorHandler {
    private val errorHandlers = mutableMapOf<String, (ApiException) -> Unit>()

    init {
        // Register default handlers
        registerHandler("AUTH_TOKEN_EXPIRED") { exception ->
            // Trigger token refresh
            CoroutineScope(Dispatchers.Main).launch {
                val authRepository = get<AuthRepository>()
                authRepository.refreshToken()
            }
        }

        registerHandler("AUTH_PERMISSION_DENIED") { exception ->
            // Navigate to unauthorized screen
            navController.navigate("unauthorized")
        }

        registerHandler("VALIDATION_ERROR") { exception ->
            // Show validation errors
            exception.details?.forEach { detail ->
                showFieldError(detail.field, detail.message)
            }
        }

        registerHandler("SYSTEM_RATE_LIMITED") { exception ->
            // Show rate limit toast
            showToast("Too many requests. Please wait.")
        }
    }

    fun handle(exception: Exception) {
        when (exception) {
            is ApiException -> {
                val handler = errorHandlers[exception.code]
                handler?.invoke(exception) ?: defaultHandler(exception)
            }
            else -> {
                defaultHandler(exception)
            }
        }
    }

    private fun defaultHandler(exception: Exception) {
        showToast(exception.message ?: "An error occurred")
    }

    fun registerHandler(code: String, handler: (ApiException) -> Unit) {
        errorHandlers[code] = handler
    }
}
```

```python
# backend/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    type: str


class ApiError(BaseModel):
    code: str
    message: str
    type: str
    details: Optional[List[ValidationErrorDetail]] = None


class ErrorResponse(BaseModel):
    error: ApiError
    meta: dict


class ErrorHandler:
    """Centralized error handler for the API"""
    
    ERROR_CODES = {
        400: "BAD_REQUEST",
        401: "AUTH_TOKEN_INVALID",
        403: "AUTH_PERMISSION_DENIED",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "SYSTEM_RATE_LIMITED",
        500: "SYSTEM_INTERNAL_ERROR",
        503: "SYSTEM_UNAVAILABLE",
    }
    
    def __init__(self):
        self.exception_handlers: dict = {}
    
    async def handle_exception(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Main exception handler"""
        
        request_id = request.state.request_id if hasattr(request.state, 'request_id') else ""
        
        if isinstance(exc, StarletteHTTPException):
            return await self.handle_http_exception(request, exc, request_id)
        
        if isinstance(exc, RequestValidationError):
            return await self.handle_validation_error(request, exc, request_id)
        
        if isinstance(exc, ApiException):
            return await self.handle_api_exception(request, exc, request_id)
        
        return await self.handle_generic_error(request, exc, request_id)
    
    async def handle_http_exception(
        self,
        request: Request,
        exc: StarletteHTTPException,
        request_id: str
    ) -> JSONResponse:
        code = self.ERROR_CODES.get(
            exc.status_code,
            f"HTTP_{exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": exc.detail,
                    "type": "http_error"
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError,
        request_id: str
    ) -> JSONResponse:
        errors = []
        
        for error in exc.errors():
            errors.append(ValidationErrorDetail(
                field=" -> ".join(str(loc) for loc in error["loc"]),
                message=error["msg"],
                type=error["type"]
            ))
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "type": "validation_error",
                    "details": [e.dict() for e in errors]
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_api_exception(
        self,
        request: Request,
        exc: "ApiException",
        request_id: str
    ) -> JSONResponse:
        logger.warning(
            f"API error: {exc.code} - {exc.message}",
            extra={"request_id": request_id, "code": exc.code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "type": exc.error_type,
                    "details": [e.dict() for e in exc.details] if exc.details else None
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_generic_error(
        self,
        request: Request,
        exc: Exception,
        request_id: str
    ) -> JSONResponse:
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "SYSTEM_INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "type": "server_error"
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )


# Custom exception class
class ApiException(Exception):
    """Custom exception for API errors"""
    
    def __init__(
        self,
        code: str,
        message: str,
        error_type: str = "api_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[ValidationErrorDetail]] = None
    ):
        self.code = code
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details
        super().__init__(message)
```

---

## 7. Deployment Architecture

### Containerized Deployment with Kubernetes

The AMAIMA system is designed for cloud-native deployment using Docker containers orchestrated by Kubernetes. This architecture provides automatic scaling, self-healing, and zero-downtime deployments. All services are stateless, enabling horizontal scaling without data migration concerns. State is persisted in PostgreSQL, Redis, and S3, which are managed as separate resources.

The deployment uses a multi-replica strategy for all services to ensure high availability. The backend runs with GPU support for model inference, with the number of GPU-enabled pods automatically scaled based on query load. The frontend and API gateway use standard CPU-based pods with horizontal pod autoscaling based on CPU and memory utilization.

Infrastructure configuration is managed through Terraform, with environment-specific variables for development, staging, and production. Secrets are managed through Kubernetes secrets or external secret management services (AWS Secrets Manager, HashiCorp Vault). All inter-service communication within the cluster uses mTLS for security.

```yaml
# k8s/deployment.yaml

apiVersion: v1
kind: Namespace
metadata:
  name: amaima
  labels:
    environment: production

---
# Backend Deployment with GPU support
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: amaima
  labels:
    app: backend
    version: v5.0.0
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 0
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v5.0.0
    spec:
      serviceAccountName: amaima-backend
      terminationGracePeriodSeconds: 30
      containers:
      - name: backend
        image: amaima/backend:v5.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 8001
          name: metrics
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: backend-config
              key: redis-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: jwt-secret
        - name: DARPA_ENABLED
          value: "true"
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
            nvidia.com/gpu: "1"
          limits:
            memory: "32Gi"
            cpu: "8"
            nvidia.com/gpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: backend
              topologyKey: kubernetes.io/hostname

---
# Backend Service
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: amaima
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: backend

---
# Horizontal Pod Autoscaler for Backend
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: amaima
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15

---
# NGINX Ingress Controller Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-ingress
  namespace: amaima
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx-ingress
  template:
    metadata:
      labels:
        app: nginx-ingress
    spec:
      containers:
      - name: nginx-ingress
        image: nginx/nginx-ingress:3.0.0
        ports:
        - containerPort: 80
          name: http
        - containerPort: 443
          name: https
        env:
        - name: NGINX_CONFIGMAP
          value: nginx-config
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "2000m"
            memory: "1Gi"

---
# Ingress with SSL and routing
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: amaima-ingress
  namespace: amaima
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/websocket-services: "backend"
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.amaima.com
    - app.amaima.com
    secretName: amaima-tls
  rules:
  - host: api.amaima.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
  - host: app.amaima.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

---

## 8. Testing Integration

### End-to-End Testing Strategy

The AMAIMA system employs a comprehensive testing strategy spanning unit tests, integration tests, and end-to-end tests. Unit tests validate individual components in isolation, using mocks for external dependencies. Integration tests verify the interaction between components, particularly the database, cache, and external services. End-to-end tests simulate real user flows across all platforms.

Test data management uses factory patterns to create test fixtures with consistent, randomized data. The test database is reset between test runs using transactions for speed or full recreation for isolation. Fixtures include realistic user data, queries, and workflows that exercise various code paths.

Continuous integration runs the full test suite on every pull request, with parallel execution for faster feedback. Tests are tagged by duration (fast, slow, integration) and by the platform they test (web, mobile, backend). Only fast tests run on every commit; slower tests run in CI before merge.

```python
# tests/conftest.py

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import get_db
from app.auth.jwt import create_access_token
from app.models.user import User

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create database session for testing"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Create authenticated test client"""
    token = create_access_token(user_id="test_user_id")
    client.headers["Authorization"] = f"Bearer {token}"
    return client

@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user in database"""
    user = User(
        id="test_user_id",
        email="test@example.com",
        name="Test User",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    return user
```

```typescript
// frontend/tests/integration.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Complete User Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear local storage and cookies
    await page.context().clearCookies();
    await page.evaluate(() => localStorage.clear());
  });

  test('user can register, login, and submit a query', async ({ page }) => {
    // 1. Register
    await page.goto('/register');
    await page.fill('input[name="name"]', 'Test User');
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // 2. Navigate to query page
    await page.click('text=New Query');
    await expect(page.locator('h1')).toContainText('New Query');

    // 3. Submit a query
    await page.fill(
      'textarea[placeholder*="Ask"]',
      'What are the main principles of quantum computing?'
    );
    await page.click('button:has-text("Submit")');

    // 4. Wait for response
    await expect(page.locator('text=quantum')).toBeVisible({ timeout: 60000 });

    // 5. Verify response metadata
    await expect(page.locator('text=Model:')).toBeVisible();
    await expect(page.locator('text=Latency:')).toBeVisible();
    await expect(page.locator('text=Confidence:')).toBeVisible();
  });

  test('WebSocket streaming updates display correctly', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to query with streaming
    await page.click('text=New Query');
    const textarea = page.locator('textarea[placeholder*="Ask"]');
    await textarea.fill('Write a detailed explanation of neural networks');
    await page.click('button:has-text("Submit")');

    // Verify streaming indicator
    await expect(page.locator('text=Streaming')).toBeVisible();

    // Verify content appears progressively
    await expect(page.locator('text=Neural networks')).toBeVisible({ timeout: 30000 });

    // Verify completion
    await expect(page.locator('text=completed')).toBeVisible({ timeout: 120000 });
  });

  test('file upload and processing', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to file upload
    await page.click('text=Upload');
    await page.setInputFiles('input[type="file"]', 'tests/fixtures/sample.pdf');

    // Verify upload progress
    await expect(page.locator('text=Upload complete')).toBeVisible({ timeout: 30000 });

    // Submit query with file
    await page.fill(
      'textarea[placeholder*="Ask"]',
      'Summarize the key points from the uploaded document'
    );
    await page.click('button:has-text("Submit"));

    // Verify response
    await expect(page.locator('text=Key Points')).toBeVisible({ timeout: 60000 });
  });
});
```

```kotlin
// android/app/src/androidTest/java/com/amaima/app/IntegrationTest.kt

@RunWith(AndroidJUnit4::class)
@LargeTest
class IntegrationTest {

    @get:Rule
    val hiltRule = HiltAndroidRule(this)

    private lateinit var authRepository: AuthRepository
    private lateinit var queryRepository: QueryRepository
    private lateinit var webSocketManager: WebSocketManager

    @Before
    fun setup() {
        hiltRule.inject()
        authRepository = AuthRepositoryImpl(...)
        queryRepository = QueryRepositoryImpl(...)
        webSocketManager = WebSocketManager(...)
    }

    @Test
    fun authenticationFlow() = runBlocking {
        // Test registration
        val registerResult = authRepository.register(
            name = "Test User",
            email = "test${System.currentTimeMillis()}@example.com",
            password = "TestPass123!"
        )

        assertTrue(registerResult.isSuccess)
        assertNotNull(registerResult.getOrNull())

        // Test login with new credentials
        val loginResult = authRepository.login(
            email = registerResult.getOrNull()!!.email,
            password = "TestPass123!"
        )

        assertTrue(loginResult.isSuccess)
        assertEquals(registerResult.getOrNull()!!.id, loginResult.getOrNull()!!.id)

        // Test logout
        val logoutResult = authRepository.logout()
        assertTrue(logoutResult.isSuccess)
    }

    @Test
    fun querySubmissionAndStreaming() = runBlocking {
        // Login
        authRepository.login("test@example.com", "password123")

        // Connect WebSocket
        webSocketManager.connect()
        delay(2000)

        assertTrue(webSocketManager.connectionState.value == ConnectionState.CONNECTED)

        // Submit streaming query
        val queryText = "Explain how quantum computing works"
        webSocketManager.submitQuery(queryText, "general")

        // Collect streaming response
        val chunks = mutableListOf<String>()
        val completionLatch = CountDownLatch(1)

        val job = launch {
            webSocketManager.messageFlow
                .filterIsInstance<WebSocketMessage.QueryUpdate>()
                .collect { message ->
                    message.data.chunk?.let { chunks.add(it) }
                    if (message.data.complete == true) {
                        completionLatch.countDown()
                        cancel()
                    }
                }
        }

        // Wait for completion or timeout
        assertTrue(completionLatch.await(120, TimeUnit.SECONDS))

        // Verify streaming
        assertTrue(chunks.isNotEmpty())
        assertTrue(chunks.joinToString(" ").contains("quantum"))

        webSocketManager.disconnect()
    }

    @Test
    fun offlineQueryQueueAndSync() = runBlocking {
        // Enable airplane mode simulation
        networkMonitor.setOnline(false)

        // Submit query while offline
        val queryResult = queryRepository.submitQuery(
            QueryRequest(query = "Offline query test", operation = "general")
        )

        // Should be queued locally
        assertTrue(queryResult.isFailure)

        // Verify query is queued
        val pendingQueries = queryDao.getPendingQueries()
        assertEquals(1, pendingQueries.size)

        // Simulate coming back online
        networkMonitor.setOnline(true)

        // Trigger sync
        val syncWorker = SyncWorker(appContext, workerParams)
        syncWorker.doWork()

        // Verify query was synced
        val syncedQueries = queryDao.getQueriesBySyncStatus(SyncStatus.SYNCED)
        assertTrue(syncedQueries.any { it.queryText.contains("Offline query test") })
    }
}
```

---

## 9. Monitoring & Observability

### Unified Observability Stack

The AMAIMA system implements a comprehensive observability strategy using Prometheus for metrics collection, Loki for log aggregation, and Jaeger for distributed tracing. This combination provides full visibility into system behavior, enabling quick diagnosis of issues and performance optimization. All telemetry data is correlated through a consistent request ID that flows across services.

Metrics are collected at each layer of the system. Backend services expose Prometheus metrics for query latency, throughput, and error rates. The API gateway captures request metrics including response times and status codes. Frontend and mobile clients report performance metrics including page load times, API call latencies, and crash reports.

Alerting is configured for critical conditions including elevated error rates, increased latency, and resource utilization thresholds. Alerts are routed through PagerDuty for on-call rotation and integrated with Slack for team visibility. Runbooks are maintained for each alert type, providing step-by-step troubleshooting guidance.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Observability Architecture                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         Metrics Collection                               │
└─────────────────────────────────────────────────────────────────────────┘

Backend Services:
  • amaima_queries_total{operation, status, complexity}
  • amaima_query_latency_seconds{operation, model}
  • amaima_model_load_latency_seconds{model_name}
  • amaima_websocket_connections{user_id}
  • amaima_cache_hit_rate{cache_type}
  • amaima_error_rate{error_type}

API Gateway (NGINX):
  • nginx_http_requests_total{status, method}
  • nginx_request_duration_seconds{status}
  • nginx_connections_active

Database:
  • postgres_query_duration_seconds
  • postgres_active_connections
  • redis_keyspace_hits_total
  • redis_memory_used_bytes

┌─────────────────────────────────────────────────────────────────────────┐
│                         Log Aggregation                                  │
└─────────────────────────────────────────────────────────────────────────┘

Fluentd DaemonSet collects logs from:
  • /var/log/containers/*backend*.log
  • /var/log/containers/*frontend*.log
  • /var/log/containers/*nginx*.log

Log format (JSON):
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "request_id": "req_abc123",
  "service": "backend",
  "message": "Query processed",
  "user_id": "user_123",
  "latency_ms": 150
}

┌─────────────────────────────────────────────────────────────────────────┐
│                         Distributed Tracing                              │
└─────────────────────────────────────────────────────────────────────────┘

Trace flow:
User Request → API Gateway → Load Balancer → Backend Instance
     ↓              ↓                ↓               ↓
  Trace ID      Trace ID         Trace ID       Trace ID
                                             (span added)

• Trace sampling: 10% of requests
• Trace propagation: W3C Trace Context
• Trace storage: Jaeger
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "AMAIMA System Overview",
    "uid": "amaima-overview",
    "tags": ["amaima", "production"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Query Throughput (RPM)",
        "type": "graph",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "sum(rate(amaima_queries_total[5m])) by (operation) * 60",
            "legendFormat": "{{operation}}"
          }
        ],
        "alert": {
          "name": "HighQueryRate",
          "conditions": [
            {
              "evaluator": {"params": [1000], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["A", "5m", "now"]},
              "reducer": {"type": "avg"}
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "1m",
          "handler": 1,
          "message": "Query rate exceeded 1000 RPM",
          "name": "High Query Rate Alert"
        }
      },
      {
        "id": 2,
        "title": "Response Latency (p95)",
        "type": "graph",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(amaima_query_latency_seconds_bucket[5m]))",
            "legendFormat": "{{operation}} - p95"
          }
        ]
      },
      {
        "id": 3,
        "title": "Active WebSocket Connections",
        "type": "stat",
        "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "sum(amaima_websocket_connections)"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"color": "red", "value": null},
                {"color": "yellow", "value": 100},
                {"color": "green", "value": 500}
              ]
            }
          }
        }
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "stat",
        "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "rate(amaima_queries_total{status=\"error\"}[5m]) / rate(amaima_queries_total[5m]) * 100"
          }
        ]
      },
      {
        "id": 5,
        "title": "Model Load Time",
        "type": "heatmap",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "rate(amaima_model_load_latency_seconds_bucket[5m])",
            "legendFormat": "{{model_name}}",
            "format": "heatmap"
          }
        ]
      }
    ],
    "annotations": {
      "list": [
        {
          "builtIn": 1,
          "datasource": {"type": "grafana", "uid": "-- Grafana --"},
          "enable": true,
          "hide": true,
          "iconColor": "rgba(0, 211, 255, 1)",
          "name": "Annotations & Alerts",
          "type": "dashboard"
        }
      ]
    }
  }
}
```

---

## 10. Complete Integration Examples

### Example: Cross-Platform Query Submission with File Attachment

This example demonstrates how a user can submit a query with file attachments from any platform and receive streaming results.

**Step 1: User selects file and enters query (Frontend)**

```typescript
// frontend/components/QueryWithFile.tsx

'use client';

import { useState, useCallback } from 'react';
import { FileUpload } from '@/components/shared/FileUpload';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/lib/websocket/useWebSocketQuery';

interface QueryWithFileProps {
  onQueryComplete?: (result: QueryResult) => void;
}

export function QueryWithFile({ onQueryComplete }: QueryWithFileProps) {
  const [query, setQuery] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const { accessToken } = useAuth();
  const { isConnected, lastMessage, submitQuery } = useWebSocket();

  const handleFilesSelected = useCallback((selectedFiles: File[]) => {
    setFiles(selectedFiles);
  }, []);

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      // Upload files first if any
      const uploadedFiles: FileMetadata[] = [];
      for (const file of files) {
        const metadata = await fileUploader.uploadFile(file, (progress) => {
          console.log(`Uploading ${file.name}: ${progress.progress}%`);
        });
        uploadedFiles.push(metadata);
      }

      // Submit query with file references
      const response = await fetch(`${API_URL}/v1/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          query,
          operation: 'analysis',
          file_ids: uploadedFiles.map((f) => f.file_id),
        }),
      });

      if (!response.ok) {
        throw new Error('Query submission failed');
      }

      const queryResult = await response.json();
      setResult(queryResult);
      onQueryComplete?.(queryResult);

      // If WebSocket is connected, also get streaming updates
      if (isConnected && queryResult.supports_streaming) {
        submitQuery(query, 'analysis');
      }
    } catch (error) {
      toast.error('Failed to submit query');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle WebSocket updates for streaming
  useEffect(() => {
    if (lastMessage?.type === 'query_update' && lastMessage.data.chunk) {
      setResult((prev) => ({
        ...prev!,
        responseText: (prev?.responseText || '') + lastMessage.data.chunk,
        isStreaming: !lastMessage.data.complete,
      }));
    }
  }, [lastMessage]);

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Your Query</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question or describe what you want to analyze..."
          className="w-full h-32 p-4 border rounded-lg resize-none"
        />
      </div>

      <FileUpload
        onUpload={handleFilesSelected}
        maxFiles={5}
        maxSize={50 * 1024 * 1024}
      />

      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((file) => (
            <Badge key={file.name} variant="secondary">
              {file.name}
            </Badge>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4">
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || !query.trim()}
          className="min-w-[120px]"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Submit Query'
          )}
        </Button>

        {isConnected && (
          <Badge variant="outline" className="text-green-600">
            <Wifi className="mr-1 h-3 w-3" />
            Live Connected
          </Badge>
        )}
      </div>

      {result && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Query Result
              <Badge>{result.model_used}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <ReactMarkdown>{result.responseText}</ReactMarkdown>
            </div>
            
            <div className="mt-4 pt-4 border-t flex gap-4 text-sm text-muted-foreground">
              <span>Latency: {result.latency_ms}ms</span>
              <span>Confidence: {Math.round(result.confidence * 100)}%</span>
              {result.file_references && (
                <span>Files analyzed: {result.file_references.length}</span>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

**Step 2: Backend processes query with file attachments**

```python
# backend/routers/query_router.py

from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/v1/query", tags=["queries"])

class QueryRequest(BaseModel):
    query: str
    operation: str = "general"
    file_ids: Optional[List[str]] = None
    context: Optional[dict] = None

class QueryResponse(BaseModel):
    query_id: str
    response_text: str
    model_used: str
    confidence: float
    latency_ms: int
    supports_streaming: bool = True
    file_references: Optional[List[dict]] = None

@router.post("", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    current_user = Depends(get_current_user)
):
    """Submit a query for processing with optional file attachments"""
    
    # Build query context
    context = request.context or {}
    
    # Process file attachments
    file_contents = []
    if request.file_ids:
        for file_id in request.file_ids:
            file_metadata = await get_file_metadata(file_id, current_user.id)
            
            if not file_metadata:
                raise ApiException(
                    code="FILE_NOT_FOUND",
                    message=f"File {file_id} not found",
                    status_code=404
                )
            
            # Download and parse file content
            file_content = await download_and_parse_file(file_metadata)
            file_contents.append({
                "filename": file_metadata.filename,
                "content": file_content,
                "type": file_metadata.mime_type
            })
            
            # Add file reference to response
            context.setdefault("file_references", []).append({
                "file_id": file_id,
                "filename": file_metadata.filename
            })
    
    # Enhance query with file contents
    enhanced_query = request.query
    if file_contents:
        file_context = "\n\n".join([
            f"--- File: {f['filename']} ---\n{f['content']}"
            for f in file_contents
        ])
        enhanced_query = f"{request.query}\n\nRelevant file contents:\n{file_context}"
    
    # Route query through smart router
    routing_decision = await smart_router.route(
        enhanced_query,
        request.operation,
        user_context={
            "user_id": current_user.id,
            "tier": current_user.subscription_tier
        }
    )
    
    # Process query with selected model
    start_time = time.time()
    response_text = await process_query_with_model(
        enhanced_query,
        routing_decision.model_name,
        context=context
    )
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Verify response quality
    verification = await verify_response(
        response_text,
        enhanced_query,
        routing_decision.model_name
    )
    
    # Log query for analytics
    await log_query(
        user_id=current_user.id,
        query=request.query,
        response=response_text,
        model=routing_decision.model_name,
        latency_ms=latency_ms,
        confidence=verification.confidence,
        file_count=len(file_contents)
    )
    
    return QueryResponse(
        query_id=str(uuid.uuid4()),
        response_text=response_text,
        model_used=routing_decision.model_name,
        confidence=verification.confidence,
        latency_ms=latency_ms,
        supports_streaming=True,
        file_references=context.get("file_references")
    )
```

**Step 3: Android implementation with coroutines and flow**

```kotlin
// android/ui/query/QueryViewModel.kt

@HiltViewModel
class QueryViewModel @Inject constructor(
    private val queryRepository: QueryRepository,
    private val fileRepository: FileRepository,
    private val webSocketManager: WebSocketManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(QueryUiState())
    val uiState: StateFlow<QueryUiState> = _uiState.asStateFlow()

    private val _queryResult = MutableStateFlow<QueryResult?>(null)
    val queryResult: StateFlow<QueryResult?> = _queryResult.asStateFlow()

    private val _streamingText = MutableStateFlow("")
    val streamingText: StateFlow<String> = _streamingText.asStateFlow()

    init {
        // Collect WebSocket messages
        viewModelScope.launch {
            webSocketManager.messageFlow.collect { message ->
                handleWebSocketMessage(message)
            }
        }
    }

    fun submitQuery(query: String, files: List<File>) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }

            try {
                // Upload files first
                val uploadedFiles = mutableListOf<FileMetadata>()
                if (files.isNotEmpty()) {
                    val uploadResult = fileRepository.uploadMultipleFiles(
                        files
                    ) { index, progress ->
                        _uiState.update {
                            it.copy(uploadProgress = progress * 100 / files.size)
                        }
                    }

                    uploadResult.fold(
                        onSuccess = { uploadedFiles.addAll(it) },
                        onFailure = { error ->
                            _uiState.update { it.copy(error = error.message) }
                            return@launch
                        }
                    )
                }

                // Submit query
                val request = QueryRequest(
                    query = query,
                    operation = "analysis",
                    fileIds = uploadedFiles.map { it.fileId },
                    context = mapOf("source" to "android")
                )

                val result = queryRepository.submitQuery(request)

                result.fold(
                    onSuccess = { queryResult ->
                        _queryResult.value = queryResult
                        _uiState.update { it.copy(isLoading = false) }

                        // Start WebSocket streaming if supported
                        if (queryResult.supportsStreaming) {
                            _uiState.update { it.copy(isStreaming = true) }
                            webSocketManager.submitQuery(query, "analysis")
                        }
                    },
                    onFailure = { error ->
                        _uiState.update {
                            it.copy(
                                isLoading = false,
                                error = error.message ?: "Query failed"
                            )
                        }
                    }
                )
            } catch (e: Exception) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        error = e.message ?: "An error occurred"
                    )
                }
            }
        }
    }

    private fun handleWebSocketMessage(message: WebSocketMessage) {
        when (message) {
            is WebSocketMessage.QueryUpdate -> {
                message.data.chunk?.let { chunk ->
                    _streamingText.update { it + chunk }
                }

                if (message.data.complete == true) {
                    _uiState.update { it.copy(isStreaming = false) }
                    // Update final result
                    _queryResult.value = _queryResult.value?.copy(
                        responseText = _streamingText.value
                    )
                }
            }
            is WebSocketMessage.Error -> {
                _uiState.update {
                    it.copy(
                        isStreaming = false,
                        error = message.message
                    )
                }
            }
            else -> {}
        }
    }

    fun clearQuery() {
        _queryResult.value = null
        _streamingText.value = ""
        _uiState.update { QueryUiState() }
    }
}

data class QueryUiState(
    val isLoading: Boolean = false,
    val isStreaming: Boolean = false,
    val uploadProgress: Float = 0f,
    val error: String? = null
)
```

---

## Summary: Integration Checklist

### ✅ Core Integration Points

| Component | Backend | Frontend | Mobile | Notes |
|-----------|---------|----------|--------|-------|
| **Authentication** | JWT + Refresh Token | Secure Storage + Auto-refresh | Keystore + WorkManager | Unified token format |
| **Real-time** | WebSocket with auth | Socket.io client | OkHttp WebSocket | Same message protocol |
| **Data Sync** | PostgreSQL + Redis | IndexedDB | Room + WorkManager | Conflict resolution |
| **File Upload** | S3 Presigned URLs | XHR Progress | Retrofit + Progress | Same validation |
| **Error Handling** | Standardized errors | Error boundaries | Exception mapping | Consistent codes |

### ✅ Critical Integration Checklist

**Authentication & Security**
- [ ] JWT token issuance and validation across all platforms
- [ ] Secure token storage (HTTP-only cookies, Keystore, Keychain)
- [ ] Automatic token refresh before expiration
- [ ] Session management with device tracking
- [ ] Rate limiting per user and endpoint

**Real-Time Communication**
- [ ] WebSocket connection establishment with authentication
- [ ] Heartbeat mechanism for connection health
- [ ] Automatic reconnection with exponential backoff
- [ ] Message queuing during disconnections
- [ ] Subscription management for targeted updates

**Data Synchronization**
- [ ] Offline operation support
- [ ] Background sync with WorkManager
- [ ] Conflict detection and resolution
- [ ] Cache invalidation strategies
- [ ] Data consistency guarantees

**Error Handling**
- [ ] Standardized error response format
- [ ] Platform-specific error handlers
- [ ] Retry logic with backoff
- [ ] User-friendly error messages
- [ ] Error logging and monitoring

**Testing & Quality**
- [ ] Integration tests for all API endpoints
- [ ] E2E tests for critical user flows
- [ ] Performance benchmarks
- [ ] Security testing (penetration testing)
- [ ] Load testing under expected traffic

**Monitoring & Observability**
- [ ] Metrics collection (Prometheus)
- [ ] Log aggregation (ELK/Loki)
- [ ] Distributed tracing (Jaeger)
- [ ] Alert configuration
- [ ] Dashboards for system health

This consolidated integration guide provides a unified approach to connecting the AMAIMA backend, frontend, and mobile clients. All platforms share the same core protocols, error formats, and data structures, enabling consistent behavior and simplified maintenance across the entire system.
