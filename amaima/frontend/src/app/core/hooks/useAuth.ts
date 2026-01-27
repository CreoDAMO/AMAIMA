'use client';

import { useAuthStore } from '@/lib/stores/useAuthStore';

export function useAuth() {
  const { user, isAuthenticated, isLoading, login, logout } = useAuthStore();
  return { user, isAuthenticated, isLoading, login, logout };
}
