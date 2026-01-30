import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queriesApi } from '@/app/core/lib/api/queries';
import { useQueryStore } from '@/app/core/lib/stores/useQueryStore';
import { useWebSocket } from '@/app/core/lib/websocket/WebSocketProvider';
import { useCallback } from 'react';
import { QuerySubmitRequest, Query } from '@/app/core/types';
import { toast } from 'sonner';

export function useSubmitQuery() {
  const queryClient = useQueryClient();
  const { addQuery } = useQueryStore();
  const { sendMessage, isConnected } = useWebSocket();

  return useMutation({
    mutationFn: (data: QuerySubmitRequest) => queriesApi.submit(data),
    onMutate: async (newQuery) => {
      await queryClient.cancelQueries({ queryKey: ['queries'] });

      const tempQuery: Query = {
        id: `temp-${Date.now()}`,
        userId: 'current-user',
        queryText: newQuery.query,
        operation: newQuery.operation,
        status: 'pending',
        createdAt: new Date().toISOString(),
      };

      addQuery(tempQuery);

      return { tempQueryId: tempQuery.id };
    },
    onSuccess: (response, variables, context) => {
      if (response.success && response.data) {
        const query = response.data;

        useQueryStore.getState().updateQuery(context?.tempQueryId || '', {
          id: query.id,
          status: 'processing',
        });

        if (isConnected && query.id) {
          sendMessage({
            type: 'subscribe_query',
            queryId: query.id,
          });
        }

        toast.success('Query submitted successfully');
      } else {
        toast.error(response.error?.message || 'Failed to submit query');
      }
    },
    onError: (error, variables, context) => {
      toast.error('Failed to submit query');
      console.error(error);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['queries'] });
    },
  });
}

export function useQueries(params?: { page?: number; limit?: number; status?: string }) {
  return useQuery({
    queryKey: ['queries', params],
    queryFn: async () => {
      const response = await queriesApi.getAll(params);
      if (response.success) {
        return response.data;
      }
      throw new Error(response.error?.message);
    },
  });
}

export function useQueryHistory(limit = 50) {
  return useQuery({
    queryKey: ['queries', 'history', limit],
    queryFn: async () => {
      const response = await queriesApi.getHistory(limit);
      if (response.success) {
        return response.data;
      }
      throw new Error(response.error?.message);
    },
  });
}

export function useQueryById(id: string) {
  return useQuery({
    queryKey: ['queries', id],
    queryFn: async () => {
      const response = await queriesApi.getById(id);
      if (response.success) {
        return response.data;
      }
      throw new Error(response.error?.message);
    },
    enabled: !!id,
  });
}

export function useCancelQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => queriesApi.cancel(id),
    onSuccess: (response, id) => {
      if (response.success) {
        queryClient.invalidateQueries({ queryKey: ['queries'] });
        toast.success('Query cancelled');
      } else {
        toast.error(response.error?.message || 'Failed to cancel query');
      }
    },
    onError: (error) => {
      toast.error('Failed to cancel query');
      console.error(error);
    },
  });
}

export function useDeleteQuery() {
  const queryClient = useQueryClient();
  const { removeQuery } = useQueryStore();

  return useMutation({
    mutationFn: (id: string) => queriesApi.delete(id),
    onSuccess: (response, id) => {
      if (response.success) {
        removeQuery(id);
        queryClient.invalidateQueries({ queryKey: ['queries'] });
        toast.success('Query deleted');
      } else {
        toast.error(response.error?.message || 'Failed to delete query');
      }
    },
  });
}
