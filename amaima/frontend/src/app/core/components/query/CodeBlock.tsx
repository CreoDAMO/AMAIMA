'use client';

import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '@/app/core/components/ui/button';
import { Check, Copy } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/app/core/lib/utils/cn';

interface CodeBlockProps {
  code: string;
  language: string;
  filename?: string;
  showLineNumbers?: boolean;
}

export function CodeBlock({
  code,
  language,
  filename,
  showLineNumbers = true,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-4 rounded-xl overflow-hidden">
      {/* Header */}
      {(filename || language) && (
        <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
          <div className="flex items-center gap-2">
            {filename && (
              <span className="text-sm text-muted-foreground">{filename}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground uppercase">{language}</span>
            <Button
              onClick={copyToClipboard}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
            >
              {copied ? (
                <Check className="h-4 w-4 text-emerald-400" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      )}

      {/* Code */}
      <div className={cn(!filename && !language && 'pt-2')}>
        <SyntaxHighlighter
          language={language}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: '1.5rem',
            background: 'rgba(0, 0, 0, 0.5)',
            fontSize: '0.875rem',
            lineHeight: '1.5',
          }}
          showLineNumbers={showLineNumbers}
          lineNumberStyle={{
            minWidth: '2.5rem',
            paddingRight: '1rem',
            color: '#6b7280',
            textAlign: 'right',
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>

      {/* Copy Button (visible on hover without header) */}
      {!filename && !language && (
        <Button
          onClick={copyToClipboard}
          size="sm"
          variant="ghost"
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          {copied ? (
            <Check className="h-4 w-4 text-emerald-400" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </Button>
      )}
    </div>
  );
}
