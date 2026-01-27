// frontend/lib/upload/file-uploader.ts

import { secureStorage } from '@/core/lib/utils/secure-storage';

interface UploadProgress {
  fileId: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

interface FileMetadata {
  file_id: string;
  filename: string;
  mime_type: string;
  size: number;
  url: string;
  checksum: string;
  upload_date: string;
}

class FileUploader {
  private readonly API_URL: string;

  constructor() {
    this.API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  async uploadFile(
    file: File,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<FileMetadata> {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress({
            fileId: 'pending',
            progress,
            status: 'uploading',
          });
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const metadata: FileMetadata = JSON.parse(xhr.responseText);
          onProgress?.({
            fileId: metadata.file_id,
            progress: 100,
            status: 'completed',
          });
          resolve(metadata);
        } else {
          const error = JSON.parse(xhr.responseText);
          onProgress?.({
            fileId: 'pending',
            progress: 0,
            status: 'error',
            error: error.error?.message || 'Upload failed',
          });
          reject(new Error(error.error?.message || `Upload failed: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        const error = new Error('Network error during upload');
        onProgress?.({
          fileId: 'pending',
          progress: 0,
          status: 'error',
          error: error.message,
        });
        reject(error);
      });

      xhr.open('POST', `${this.API_URL}/v1/files/upload`);
      xhr.setRequestHeader(
        'Authorization',
        `Bearer ${secureStorage.getItem('access_token')}`
      );
      xhr.send(formData);
    });
  }

  async uploadMultipleFiles(
    files: File[],
    onProgress?: (progress: UploadProgress) => void
  ): Promise<FileMetadata[]> {
    const results: FileMetadata[] = [];
    const errors: Error[] = [];

    for (const file of files) {
      try {
        const result = await this.uploadFile(file, onProgress);
        results.push(result);
      } catch (error) {
        errors.push(error as Error);
      }
    }

    if (results.length === 0 && errors.length > 0) {
      throw errors[0];
    }

    return results;
  }

  async getPresignedUrl(fileId: string): Promise<string> {
    const response = await fetch(`${this.API_URL}/v1/files/${fileId}`, {
      headers: {
        Authorization: `Bearer ${secureStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get file URL');
    }

    const metadata: FileMetadata = await response.json();
    return metadata.url;
  }

  async deleteFile(fileId: string): Promise<void> {
    const response = await fetch(`${this.API_URL}/v1/files/${fileId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${secureStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to delete file');
    }
  }

  async downloadFile(fileId: string, filename?: string): Promise<void> {
    const url = await this.getPresignedUrl(fileId);
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error('Failed to download file');
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  validateFile(file: File, options: UploadValidationOptions): ValidationResult {
    const errors: string[] = [];
    const maxSize = options.maxSize || 50 * 1024 * 1024;

    // Check file size
    if (file.size > maxSize) {
      errors.push(
        `File too large. Maximum size is ${(maxSize / (1024 * 1024)).toFixed(0)}MB`
      );
    }

    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (options.allowedExtensions && !options.allowedExtensions.includes(extension)) {
      errors.push(
        `File type ${extension} not allowed. Allowed types: ${options.allowedExtensions.join(', ')}`
      );
    }

    // Check MIME type
    if (options.allowedMimeTypes && !options.allowedMimeTypes.includes(file.type)) {
      errors.push(`MIME type ${file.type} not allowed`);
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

interface UploadValidationOptions {
  maxSize?: number;
  allowedExtensions?: string[];
  allowedMimeTypes?: string[];
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export const fileUploader = new FileUploader();
