// frontend/lib/api/error-handler.ts
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';

const authStore = {
  getState: () => ({
    refreshToken: async () => true
  })
};

const router = {
  push: (path: string) => console.log('Redirecting to', path)
};

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

  errorHandlers.set('AUTH_TOKEN_EXPIRED', () => {
    authStore.getState().refreshToken();
  });

  errorHandlers.set('AUTH_PERMISSION_DENIED', () => {
    router.push('/unauthorized');
  });

  errorHandlers.set('VALIDATION_ERROR', (error) => {
    error.details?.forEach((detail) => {
      const fieldElement = document.querySelector(`[name="${detail.field}"]`);
      if (fieldElement) {
        fieldElement.classList.add('error');
        fieldElement.setAttribute('data-error', detail.message);
      }
    });
  });

  errorHandlers.set('SYSTEM_RATE_LIMITED', (error) => {
    toast.error('Too many requests. Please wait before trying again.');
  });

  errorHandlers.set('SYSTEM_UNAVAILABLE', () => {
    toast.error('Service temporarily unavailable. Retrying...');
  });

  return {
    handle(error: unknown, context?: string): ApiError | null {
      let apiError: ApiError;
      if (ApiError.isApiError(error)) {
        apiError = error as ApiError;
      } else if (error instanceof Error && error.message) {
        apiError = new ApiError({
          error: { code: 'UNKNOWN_ERROR', message: error.message, type: 'unknown' },
          meta: { request_id: '', timestamp: new Date().toISOString(), path: context || '' },
        });
      } else {
        apiError = new ApiError({
          error: { code: 'UNKNOWN_ERROR', message: 'An unknown error occurred', type: 'unknown' },
          meta: { request_id: '', timestamp: new Date().toISOString(), path: context || '' },
        });
      }
      console.error('API Error:', { code: apiError.code, message: apiError.message, path: apiError.path, requestId: apiError.requestId });
      const handler = errorHandlers.get(apiError.code);
      if (handler) {
        handler(apiError);
      } else if (apiError.code.startsWith('SYSTEM_')) {
        errorHandlers.get('SYSTEM_UNAVAILABLE')?.(apiError);
      }
      return apiError;
    },
    registerHandler(code: string, handler: (error: ApiError) => void) { errorHandlers.set(code, handler); },
    removeHandler(code: string) { errorHandlers.delete(code); },
  };
}
