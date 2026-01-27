// frontend/lib/sync/sync-manager.ts

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { queryClient } from '@/lib/query/client';
import { secureStorage } from '@/lib/utils/secure-storage';

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
    } as any);
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
