/**
 * ChatMessage Component - Individual message display in conversation
 */

import React from 'react';
import { Copy, Share2 } from 'lucide-react';
import { Button } from '../common';

export type MessageRole = 'user' | 'assistant' | 'system';

interface ChatMessageProps {
  role: MessageRole;
  content: string;
  timestamp?: Date;
  onCopy?: () => void;
  onShare?: () => void;
  isFaded?: boolean; // For displaying previous conversation with reduced opacity
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  timestamp,
  onCopy,
  onShare,
  isFaded = false,
}) => {
  const isUser = role === 'user';

  const roleColors = {
    user: 'bg-blue-50 dark:bg-blue-900',
    assistant: 'bg-gray-50 dark:bg-gray-800',
    system: 'bg-yellow-50 dark:bg-yellow-900',
  };

  const roleBorders = {
    user: 'border-blue-200 dark:border-blue-700',
    assistant: 'border-gray-200 dark:border-gray-700',
    system: 'border-yellow-200 dark:border-yellow-700',
  };

  const textColors = {
    user: 'text-blue-900 dark:text-blue-100',
    assistant: 'text-gray-900 dark:text-gray-100',
    system: 'text-yellow-900 dark:text-yellow-100',
  };

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 ${isFaded ? 'opacity-60' : ''} transition-opacity`}
    >
      <div
        className={`max-w-sm md:max-w-xl lg:max-w-2xl xl:max-w-3xl ${roleColors[role]} ${roleBorders[role]} border rounded-lg p-3`}
      >
        <div className={`text-sm ${textColors[role]} whitespace-pre-wrap break-words`}>
          {content}
        </div>

        {timestamp && (
          <div className={`text-xs mt-2 ${textColors[role]} opacity-70`}>
            {timestamp.toLocaleTimeString()}
          </div>
        )}

        {(onCopy || onShare) && (
          <div className="flex gap-1 mt-2 -mx-1">
            {onCopy && (
              <button
                onClick={onCopy}
                className={`p-1 rounded text-xs ${textColors[role]} hover:opacity-70 transition-opacity`}
                title="Copy message"
              >
                <Copy className="h-3 w-3" />
              </button>
            )}
            {onShare && (
              <button
                onClick={onShare}
                className={`p-1 rounded text-xs ${textColors[role]} hover:opacity-70 transition-opacity`}
                title="Share message"
              >
                <Share2 className="h-3 w-3" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

ChatMessage.displayName = 'ChatMessage';
