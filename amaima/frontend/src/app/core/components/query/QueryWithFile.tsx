// frontend/components/query/QueryWithFile.tsx

'use client';

import { useState, useCallback, useEffect } from 'react';
import { Badge } from '@/app/core/components/ui/badge';
import { Button } from '@/app/core/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/app/core/components/ui/card';
import { Loader2, Wifi } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { toast } from 'sonner';
import { WebSocketMessage } from '@/app/core/types';

// Mock components and hooks that are missing or causing issues
const FileUpload = ({ onUpload }: any) => null;
const useAuth = () => ({ accessToken: '' });
const useWebSocket = () => ({
  isConnected: false,
  lastMessage: null as WebSocketMessage | null,
  submitQuery: (q: string, o: string) => {}
});

interface QueryResult {
  responseText: string;
  isStreaming: boolean;
  model_used: string;
  latency_ms: number;
  confidence: number;
  file_references?: any[];
  supports_streaming?: boolean;
}

interface FileMetadata {
  file_id: string;
  name: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';
const fileUploader = {
  uploadFile: async (file: File, onProgress: (p: { progress: number }) => void) => {
    return { file_id: 'mock-id', name: file.name };
  }
};

interface QueryWithFileProps {
  onQueryComplete?: (result: QueryResult) => void;
}

export function QueryWithFile({ onQueryComplete }: QueryWithFileProps) {
  const [query, setQuery] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const { accessToken } = useAuth();
  const { isConnected, lastMessage, submitQuery } = useWebSocket();

  const handleFilesSelected = useCallback((selectedFiles: File[]) => {
    setFiles(selectedFiles);
  }, []);

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast.error('Please enter a query');
      return;
    }

    setIsSubmitting(true);
    setResult(null);

    try {
      // Upload files first if any
      const uploadedFiles: FileMetadata[] = [];
      for (const file of files) {
        const metadata = await fileUploader.uploadFile(file, (progress) => {
          console.log(`Uploading ${file.name}: ${progress.progress}%`);
        });
        uploadedFiles.push(metadata);
      }

      // Submit query with file references
      const response = await fetch(`${API_URL}/v1/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          query,
          operation: 'analysis',
          file_ids: uploadedFiles.map((f) => f.file_id),
        }),
      });

      if (!response.ok) {
        throw new Error('Query submission failed');
      }

      const queryResult = await response.json();
      setResult(queryResult);
      onQueryComplete?.(queryResult);

      // If WebSocket is connected, also get streaming updates
      if (isConnected && queryResult.supports_streaming) {
        submitQuery(query, 'analysis');
      }
    } catch (error) {
      toast.error('Failed to submit query');
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle WebSocket updates for streaming
  useEffect(() => {
    if (lastMessage?.type === 'query_update' && lastMessage.data.chunk) {
      setResult((prev) => ({
        ...prev!,
        responseText: (prev?.responseText || '') + lastMessage.data.chunk,
        isStreaming: !lastMessage.data.complete,
      }));
    }
  }, [lastMessage]);

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium mb-2">Your Query</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question or describe what you want to analyze..."
          className="w-full h-32 p-4 border rounded-lg resize-none"
        />
      </div>

      <FileUpload
        onUpload={handleFilesSelected}
        maxFiles={5}
        maxSize={50 * 1024 * 1024}
      />

      {files.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {files.map((file) => (
            <Badge key={file.name} variant="secondary">
              {file.name}
            </Badge>
          ))}
        </div>
      )}

      <div className="flex items-center gap-4">
        <Button
          onClick={handleSubmit}
          disabled={isSubmitting || !query.trim()}
          className="min-w-[120px]"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            'Submit Query'
          )}
        </Button>

        {isConnected && (
          <Badge variant="outline" className="text-green-600">
            <Wifi className="mr-1 h-3 w-3" />
            Live Connected
          </Badge>
        )}
      </div>

      {result && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Query Result
              <Badge>{result.model_used}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <ReactMarkdown>{result.responseText}</ReactMarkdown>
            </div>
            
            <div className="mt-4 pt-4 border-t flex gap-4 text-sm text-muted-foreground">
              <span>Latency: {result.latency_ms}ms</span>
              <span>Confidence: {Math.round(result.confidence * 100)}%</span>
              {result.file_references && (
                <span>Files analyzed: {result.file_references.length}</span>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
