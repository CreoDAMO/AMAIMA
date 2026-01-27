import { apiClient } from '@/core/lib/api/client';
import { Query, QuerySubmitRequest, ApiResponse } from '@/core/types';

export const queriesApi = {
  submit: async (data: QuerySubmitRequest): Promise<ApiResponse<Query>> => {
    return apiClient.post<Query>('/v1/queries', data);
  },

  getAll: async (params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<ApiResponse<Query[]>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.status) searchParams.set('status', params.status);

    const query = searchParams.toString();
    return apiClient.get<Query[]>(`/v1/queries${query ? `?${query}` : ''}`);
  },

  getById: async (id: string): Promise<ApiResponse<Query>> => {
    return apiClient.get<Query>(`/v1/queries/${id}`);
  },

  cancel: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.post<void>(`/v1/queries/${id}/cancel`, {});
  },

  delete: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete(`/v1/queries/${id}`);
  },

  getHistory: async (limit = 50): Promise<ApiResponse<Query[]>> => {
    return apiClient.get<Query[]>(`/v1/queries/history?limit=${limit}`);
  },
};
