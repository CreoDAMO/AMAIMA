import { create } from 'zustand';
import { Query, QueryStatus } from '@/core/types';

interface QueryStore {
  queries: Query[];
  activeQueryId: string | null;
  isStreaming: boolean;
  
  addQuery: (query: Query) => void;
  updateQuery: (id: string, updates: Partial<Query>) => void;
  updateQueryStatus: (id: string, status: QueryStatus) => void;
  appendResponseChunk: (id: string, chunk: string) => void;
  setActiveQuery: (id: string | null) => void;
  setStreaming: (isStreaming: boolean) => void;
  removeQuery: (id: string) => void;
  clearAllQueries: () => void;
}

export const useQueryStore = create<QueryStore>((set, get) => ({
  queries: [],
  activeQueryId: null,
  isStreaming: false,

  addQuery: (query: Query) => {
    set((state) => ({
      queries: [query, ...state.queries],
      activeQueryId: query.id,
    }));
  },

  updateQuery: (id: string, updates: Partial<Query>) => {
    set((state) => ({
      queries: state.queries.map((q) =>
        q.id === id ? { ...q, ...updates } : q
      ),
    }));
  },

  updateQueryStatus: (id: string, status: QueryStatus) => {
    set((state) => ({
      queries: state.queries.map((q) =>
        q.id === id
          ? {
              ...q,
              status,
              completedAt: status === 'completed' || status === 'failed' 
                ? new Date().toISOString() 
                : q.completedAt,
            }
          : q
      ),
    }));
  },

  appendResponseChunk: (id: string, chunk: string) => {
    set((state) => ({
      queries: state.queries.map((q) =>
        q.id === id
          ? {
              ...q,
              responseText: (q.responseText || '') + chunk,
            }
          : q
      ),
    }));
  },

  setActiveQuery: (id: string | null) => {
    set({ activeQueryId: id });
  },

  setStreaming: (isStreaming: boolean) => {
    set({ isStreaming });
  },

  removeQuery: (id: string) => {
    set((state) => ({
      queries: state.queries.filter((q) => q.id !== id),
      activeQueryId: state.activeQueryId === id ? null : state.activeQueryId,
    }));
  },

  clearAllQueries: () => {
    set({ queries: [], activeQueryId: null });
  },
}));
