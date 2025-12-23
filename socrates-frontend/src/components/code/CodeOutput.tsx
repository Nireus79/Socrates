/**
 * CodeOutput Component - Display generated code with actions
 */

import React from 'react';
import { Copy, Download, Share2, Check, Maximize2 } from 'lucide-react';
import { Card, Button, Badge } from '../common';

interface CodeOutputProps {
  code: string;
  language: string;
  onAccept?: () => void;
  onRegenerate?: () => void;
  onCopy?: () => void;
  isFullScreen?: boolean;
  onToggleFullScreen?: () => void;
}

export const CodeOutput: React.FC<CodeOutputProps> = ({
  code,
  language,
  onAccept,
  onRegenerate,
  onCopy,
  isFullScreen = false,
  onToggleFullScreen,
}) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    onCopy?.();
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    const file = new Blob([code], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `code.${getFileExtension(language)}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const getFileExtension = (lang: string): string => {
    const extensions: Record<string, string> = {
      python: 'py',
      javascript: 'js',
      typescript: 'ts',
      java: 'java',
      cpp: 'cpp',
      csharp: 'cs',
      go: 'go',
      rust: 'rs',
      php: 'php',
    };
    return extensions[lang] || 'txt';
  };

  return (
    <Card className={isFullScreen ? 'fixed inset-0 z-50 rounded-none' : ''}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <Badge variant="primary">{language.toUpperCase()}</Badge>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {code.split('\n').length} lines
            </span>
          </div>

          <div className="flex gap-2">
            {onToggleFullScreen && (
              <Button
                variant="ghost"
                icon={<Maximize2 className="h-4 w-4" />}
                onClick={onToggleFullScreen}
                title="Toggle fullscreen"
              />
            )}
          </div>
        </div>

        {/* Code Display */}
        <div
          className={`flex-1 overflow-auto bg-gray-900 dark:bg-gray-950 rounded-lg p-4 font-mono text-sm text-gray-100 ${
            isFullScreen ? 'mb-4' : 'mb-4'
          }`}
        >
          <pre className="whitespace-pre-wrap break-words">{code}</pre>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-4 border-t border-gray-200 dark:border-gray-700 flex-wrap">
          <Button
            variant="secondary"
            icon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            onClick={handleCopy}
          >
            {copied ? 'Copied!' : 'Copy'}
          </Button>

          <Button
            variant="secondary"
            icon={<Download className="h-4 w-4" />}
            onClick={handleDownload}
          >
            Download
          </Button>

          <Button
            variant="secondary"
            icon={<Share2 className="h-4 w-4" />}
            onClick={() => console.log('Share')}
          >
            Share
          </Button>

          <div className="flex-1" />

          {onRegenerate && (
            <Button variant="outline" onClick={onRegenerate}>
              Regenerate
            </Button>
          )}

          {onAccept && (
            <Button variant="primary" onClick={onAccept}>
              Accept & Save
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

CodeOutput.displayName = 'CodeOutput';
