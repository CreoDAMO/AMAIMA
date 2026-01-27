'use client';

import { useState, useEffect, useTransition } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/core/components/ui/card';
import { Button } from '@/core/components/ui/button';
import { Textarea } from '@/core/components/ui/textarea';
import { Badge } from '@/core/components/ui/badge';
import { Loader2, Send, Sparkles, Zap, Brain, Code } from 'lucide-react';
import { complexityEstimator } from '@/core/lib/ml/complexity-estimator';
import { useWebSocket } from '@/core/lib/websocket/WebSocketProvider';
import { useSubmitQuery } from '@/core/hooks/useQuery';
import { useComplexityEstimation } from '@/core/hooks/useMLInference';
import { cn } from '@/core/lib/utils/cn';
import { QueryOperation } from '@/core/types';
import { toast } from 'sonner';

export function QueryInput() {
  const [query, setQuery] = useState('');
  const [operation, setOperation] = useState<QueryOperation>('general');
  const [isPending, startTransition] = useTransition();
  const { isConnected } = useWebSocket();
  const submitMutation = useSubmitQuery();
  const { result: complexityResult, isLoading: isEstimating } = useComplexityEstimation(query);
  const complexity = (complexityResult as any)?.complexity ? (complexityResult as any) : null;

  const operationIcons: Record<QueryOperation, React.ReactNode> = {
    general: <Brain className="h-4 w-4" />,
    code_generation: <Code className="h-4 w-4" />,
    analysis: <Sparkles className="h-4 w-4" />,
    translation: <Zap className="h-4 w-4" />,
    creative: <Sparkles className="h-4 w-4" />,
  };

  const handleSubmit = async () => {
    if (!query.trim()) return;

    startTransition(() => {
      submitMutation.mutate(
        {
          query,
          operation,
          preferences: {
            streaming: isConnected,
          },
        },
        {
          onError: (error) => {
            toast.error('Failed to submit query');
            console.error(error);
          },
        }
      );
    });
  };

  const getComplexityColor = (level: string) => {
    const colors: Record<string, string> = {
      TRIVIAL: 'emerald',
      SIMPLE: 'cyan',
      MODERATE: 'amber',
      COMPLEX: 'purple',
      EXPERT: 'pink',
    };
    return colors[level] || 'default';
  };

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-cyan-400" />
          New Query
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Operation Selector */}
        <div className="flex flex-wrap gap-2">
          {(['general', 'code_generation', 'analysis', 'translation', 'creative'] as QueryOperation[]).map(
            (op) => (
              <Button
                key={op}
                variant={operation === op ? 'neon' : 'ghost'}
                size="sm"
                onClick={() => setOperation(op)}
                className="gap-2"
              >
                {operationIcons[op]}
                <span className="capitalize">{op.replace('_', ' ')}</span>
              </Button>
            )
          )}
        </div>

        {/* Text Input */}
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe what you want to accomplish..."
          className="min-h-[150px] resize-none text-base"
          disabled={isPending}
        />

        {/* Complexity Indicator */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2 min-h-[32px]">
            {complexity && (
              <>
                <Badge variant={getComplexityColor(complexity.complexity) as any}>
                  {complexity.complexity}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {(complexity.confidence * 100).toFixed(0)}% confidence
                </span>
                <span className="text-sm text-muted-foreground">•</span>
                <span className="text-sm text-muted-foreground">
                  ~{complexity.estimatedTokens} tokens
                </span>
                <Badge variant="outline">{complexity.suggestedModel}</Badge>
              </>
            )}
            {isEstimating && <Loader2 className="h-4 w-4 animate-spin text-cyan-400" />}
          </div>

          <div className="flex items-center gap-3">
            {/* Connection Status */}
            <div className="flex items-center gap-2 text-xs">
              <div
                className={cn(
                  'h-2 w-2 rounded-full',
                  isConnected
                    ? 'bg-emerald-500 animate-pulse'
                    : 'bg-gray-400'
                )}
              />
              <span className="text-muted-foreground">
                {isConnected ? 'Live' : 'Offline'}
              </span>
            </div>

            {/* Submit Button */}
            <Button
              onClick={handleSubmit}
              disabled={!query.trim() || isPending || submitMutation.isPending}
              variant="neon"
              loading={isPending || submitMutation.isPending}
            >
              <Send className="mr-2 h-4 w-4" />
              Submit Query
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
