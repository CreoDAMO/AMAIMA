'use client';

import { useEffect, useState } from 'react';
import { useWebSocket } from '@/core/lib/websocket/WebSocketProvider';
import { Card } from '@/core/components/ui/card';
import { Badge } from '@/core/components/ui/badge';
import { Skeleton } from '@/core/components/ui/skeleton';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, XCircle, Clock, Copy, Share2, ThumbsUp, ThumbsDown } from 'lucide-react';
import Markdown from 'react-markdown';
import { CodeBlock } from './CodeBlock';
import { Query } from '@/core/types';

interface StreamingResponseProps {
  queryId: string;
  initialQuery?: Query;
}

export function StreamingResponse({ queryId, initialQuery }: StreamingResponseProps) {
  const [content, setContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(true);
  const [isComplete, setIsComplete] = useState(false);
  const { lastMessage } = useWebSocket();

  useEffect(() => {
    if (!lastMessage || lastMessage.type !== 'query_update') return;

    const { queryId: msgQueryId, chunk, complete, responseText, status } = lastMessage.data;

    if (msgQueryId === queryId) {
      if (chunk) {
        setContent((prev) => prev + chunk);
      }
      if (responseText) {
        setContent(responseText);
      }
      if (complete || status === 'completed') {
        setIsStreaming(false);
        setIsComplete(true);
      }
      if (status === 'failed') {
        setIsStreaming(false);
      }
    }
  }, [lastMessage, queryId]);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(content);
  };

  if (isStreaming && !content) {
    return (
      <Card className="p-6 space-y-4">
        <div className="flex items-center gap-4">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-2/3" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
          <Skeleton className="h-8 w-20" />
        </div>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <AnimatePresence mode="wait">
            {isComplete ? (
              <motion.div
                key="complete"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
              >
                <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              </motion.div>
            ) : (
              <motion.div
                key="streaming"
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                className="flex items-center gap-2"
              >
                <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="text-sm text-cyan-400">Streaming...</span>
              </motion.div>
            )}
          </AnimatePresence>

          {initialQuery?.modelUsed && (
            <Badge variant="glass">{initialQuery.modelUsed}</Badge>
          )}
          {initialQuery?.latencyMs && (
            <Badge variant="outline" className="gap-1">
              <Clock className="h-3 w-3" />
              {initialQuery.latencyMs}ms
            </Badge>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          <ActionButton icon={Copy} onClick={copyToClipboard} label="Copy" />
          <ActionButton icon={Share2} onClick={() => {}} label="Share" />
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        <div className="prose prose-invert max-w-none">
          <Markdown
            components={{
              code({ node, inline, className, children, ...props }: any) {
                const match = /language-(\w+)/.exec(className || '');
                const isInline = inline || !match;

                if (!isInline) {
                  return (
                    <CodeBlock
                      code={String(children).replace(/\n$/, '')}
                      language={match[1] || 'text'}
                    />
                  );
                }

                return (
                  <code className="bg-white/10 px-1.5 py-0.5 rounded text-sm" {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </Markdown>
        </div>
      </div>

      {/* Footer with Feedback */}
      {isComplete && (
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-white/5">
          <span className="text-sm text-muted-foreground">
            Was this response helpful?
          </span>
          <div className="flex items-center gap-2">
            <ActionButton icon={ThumbsUp} onClick={() => {}} label="Good" />
            <ActionButton icon={ThumbsDown} onClick={() => {}} label="Bad" />
          </div>
        </div>
      )}
    </Card>
  );
}

function ActionButton({
  icon: Icon,
  onClick,
  label,
}: {
  icon: any;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className="p-2 rounded-lg hover:bg-white/10 transition-colors"
      title={label}
    >
      <Icon className="h-4 w-4 text-muted-foreground hover:text-white" />
    </button>
  );
}
