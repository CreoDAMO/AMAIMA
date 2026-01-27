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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
