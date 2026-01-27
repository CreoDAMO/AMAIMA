// src/app/core/lib/api/error-handler.ts
import { toast } from 'sonner';

export class ApiError extends Error {
  code: string;
  type: string;
  requestId?: string;
  path?: string;

  constructor(message: string, code: string, type: string, requestId?: string, path?: string) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.type = type;
    this.requestId = requestId;
    this.path = path;
  }

  static isApiError(error: any): error is ApiError {
    return error instanceof ApiError || (error && typeof error === 'object' && 'code' in error && 'message' in error);
  }
}

export const createErrorHandler = () => ({
  handle: (error: any) => {
    const message = error?.message || 'An error occurred';
    toast.error(message);
    console.error('API Error:', error);
    return null;
  }
});
