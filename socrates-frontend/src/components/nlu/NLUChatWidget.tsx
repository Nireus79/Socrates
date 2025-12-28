/**
 * NLU Chat Widget - Reusable component for NLU chat on any page
 *
 * Provides a collapsible/expandable NLU chat interface that can be added to any page.
 * Allows users to interact with the system via natural language from anywhere.
 */

import React from 'react';
import { MessageSquare, X, Send } from 'lucide-react';
import { nluAPI } from '../../api/nlu';
import { LoadingSpinner } from '../common';

interface NLUChatWidgetProps {
  /**
   * Whether the widget should be shown by default
   * @default false
   */
  initiallyOpen?: boolean;

  /**
   * Optional context to pass to NLU interpreter
   * e.g., { project_id: "...", user_id: "..." }
   */
  context?: Record<string, any>;

  /**
   * Callback when a command is interpreted and should be executed
   */
  onCommandExecute?: (command: string) => void;

  /**
   * CSS class to apply to the widget container
   */
  className?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  type?: 'command' | 'suggestion' | 'message';
}

export const NLUChatWidget: React.FC<NLUChatWidgetProps> = ({
  initiallyOpen = false,
  context,
  onCommandExecute,
  className = '',
}) => {
  const [isOpen, setIsOpen] = React.useState(initiallyOpen);
  const [input, setInput] = React.useState('');
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userInput = input.trim();

    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userInput }]);
    setInput('');

    // If input starts with /, treat as direct command
    if (userInput.startsWith('/')) {
      const commandMsg = `Executing: ${userInput}`;
      setMessages(prev => [...prev, { role: 'assistant', content: commandMsg, type: 'command' }]);
      onCommandExecute?.(userInput);
      return;
    }

    // Otherwise, use NLU to interpret
    setIsLoading(true);
    try {
      const result = await nluAPI.interpret(userInput, context);

      if (result.status === 'success' && result.command) {
        // High confidence match
        const responseMsg = `🎯 Understood! Executing: ${result.command}`;
        setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'command' }]);
        onCommandExecute?.(result.command);
      } else if (result.status === 'suggestions' && result.suggestions && result.suggestions.length > 0) {
        // Medium confidence - show suggestions
        const suggestionText = result.suggestions
          .slice(0, 3)
          .map((s, i) => `${i + 1}. ${s.command} (${Math.round(s.confidence * 100)}%) - ${s.reasoning}`)
          .join('\n');
        const responseMsg = `I found a few possibilities:\n${suggestionText}`;
        setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'suggestion' }]);
      } else {
        // No match - provide help
        const responseMsg = result.message || "I didn't understand that. Try typing a command like /help or describe what you want.";
        setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'message' }]);
      }
    } catch (error) {
      console.error('NLU error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        type: 'message'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 p-4 bg-gradient-to-br from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all z-40 ${className}`}
        title="Open NLU Chat"
      >
        <MessageSquare size={24} />
      </button>
    );
  }

  return (
    <div className={`fixed bottom-6 right-6 w-96 h-96 bg-white dark:bg-gray-800 rounded-lg shadow-xl flex flex-col z-50 border border-gray-200 dark:border-gray-700 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900 dark:to-blue-900 rounded-t-lg">
        <div className="flex items-center gap-2">
          <MessageSquare size={20} className="text-purple-600 dark:text-purple-400" />
          <h3 className="font-semibold text-gray-900 dark:text-white">Ask Socrates</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        >
          <X size={20} />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
            <div>
              <p className="text-sm font-medium">Start a conversation</p>
              <p className="text-xs mt-1">Ask anything or type /help</p>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-bl-none'
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{msg.content}</p>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-900 rounded-b-lg">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            placeholder="Ask anything..."
            className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white disabled:opacity-50"
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !input.trim()}
            className="p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
