'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/app/core/lib/api/client';
import { AuthProvider } from '@/app/core/lib/auth/auth-provider';
import { WebSocketProvider } from '@/app/core/lib/websocket/WebSocketProvider';
import { Toaster } from 'sonner';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WebSocketProvider>
          {children}
          <Toaster position="bottom-right" />
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
