'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { secureStorage } from '@/core/lib/utils/secure-storage';
import { apiClient } from '@/core/lib/api/client';
import { User, ApiResponse } from '@/core/types';

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

  useEffect(() => {
    const init = async () => {
      try {
        const token = secureStorage.getItem('access_token');
        if (token) {
          const res = await apiClient.get<any>('/v1/auth/me');
          if (res.success && res.data?.user) {
            setUser(res.data.user);
          }
        }
      } catch (e) {
        console.error('Auth init failed', e);
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  async function login(email: string, password: string) {
    const res = await apiClient.post<any>('/v1/auth/login', { email, password });
    if (res.success && res.data) {
      secureStorage.setItem('access_token', res.data.access_token);
      secureStorage.setItem('refresh_token', res.data.refresh_token);
      apiClient.setAuthToken(res.data.access_token);
      setUser(res.data.user);
      router.push('/dashboard');
    }
  }

  async function logout() {
    secureStorage.removeItem('access_token');
    secureStorage.removeItem('refresh_token');
    apiClient.clearAuthToken();
    setUser(null);
    router.push('/login');
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, refreshToken: async () => true }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}
