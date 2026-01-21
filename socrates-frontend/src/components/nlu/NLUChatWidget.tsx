/**
 * NLU Chat Widget - Reusable component for NLU chat on any page
 *
 * Provides a collapsible/expandable NLU chat interface that can be added to any page.
 * Allows users to interact with the system via natural language from anywhere.
 */

import React from 'react';
import { MessageSquare, X, Send } from 'lucide-react';
import { nluAPI } from '../../api/nlu';
import { freeSessionAPI } from '../../api/freeSession';
import { authAPI } from '../../api/auth';
import { apiClient } from '../../api/client';
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
  const [sessionId, setSessionId] = React.useState<string>(() => {
    // Generate or retrieve session ID
    const stored = localStorage.getItem('nlu_session_id');
    if (stored) return stored;
    const newId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('nlu_session_id', newId);
    return newId;
  });
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
      const cmd = userInput.toLowerCase().trim();

      console.log('[NLUWidget] Processing command:', cmd);

      // Handle help, info, status locally in widget
      if (cmd === '/help') {
        console.log('[NLUWidget] Showing help');
        const helpText = `Available Commands:
• /help - Show this help message
• /dashboard - Go to dashboard
• /projects - Go to projects
• /chat - Open chat
• /notes - Open notes
• /knowledge - Open knowledge base
• /analytics - Open analytics
• /search - Open search
• /info - Show system information
• /status - Show system status
• /debug on|off|status - Toggle debug mode
• /subscription testing-mode on|off - Enable/disable testing mode (admin)`;
        setMessages(prev => [...prev, { role: 'assistant', content: helpText, type: 'command' }]);
        return;
      }

      if (cmd === '/info' || cmd === '/status') {
        console.log('[NLUWidget] Showing info');
        const infoText = 'Socrates - AI-Powered Development Platform\n\nStatus: Online\n\nYour AI coding assistant is ready to help you build, analyze, and improve your projects.';
        setMessages(prev => [...prev, { role: 'assistant', content: infoText, type: 'command' }]);
        return;
      }

      // Hidden command: /subscription testing-mode on/off
      if (cmd.startsWith('/subscription testing-mode')) {
        console.log('[NLUWidget] Testing mode command detected');
        const mode = cmd.replace('/subscription testing-mode', '').trim().toLowerCase();

        if (mode === 'on') {
          try {
            // Call backend to set testing mode persistently
            await authAPI.setTestingMode(true);

            // Also set localStorage for transient use (in case backend call fails)
            localStorage.setItem('socrates_testing_mode', 'enabled');
            localStorage.setItem('socrates_testing_mode_expires', (Date.now() + 24 * 60 * 60 * 1000).toString());

            const msg = '✓ Testing mode enabled for 24 hours.\n\nFeatures unlocked for testing:\n• Unlimited projects\n• All subscription tiers\n• Testing utilities enabled';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
            console.log('[Testing Mode] Enabled (backend + localStorage)');
          } catch (error) {
            console.error('[Testing Mode] Failed to enable:', error);
            const msg = '❌ Failed to enable testing mode. Please check your connection and try again.';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
          }
          return;
        } else if (mode === 'off') {
          try {
            // Call backend to disable testing mode
            await authAPI.setTestingMode(false);

            // Also clear localStorage
            localStorage.removeItem('socrates_testing_mode');
            localStorage.removeItem('socrates_testing_mode_expires');

            const msg = '✓ Testing mode disabled.\n\nNormal subscription rules apply.';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
            console.log('[Testing Mode] Disabled (backend + localStorage)');
          } catch (error) {
            console.error('[Testing Mode] Failed to disable:', error);
            const msg = '❌ Failed to disable testing mode. Please check your connection and try again.';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
          }
          return;
        } else {
          const status = localStorage.getItem('socrates_testing_mode') === 'enabled' ? 'ON' : 'OFF';
          const msg = `Testing mode is currently: ${status}\n\nUsage: /subscription testing-mode on|off`;
          setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
          return;
        }
      }

      // Debug command: /debug on/off/status
      if (cmd.startsWith('/debug')) {
        console.log('[NLUWidget] Debug command detected');
        const mode = cmd.replace('/debug', '').trim().toLowerCase();

        try {
          if (mode === 'on') {
            await apiClient.post('/debug/toggle?enabled=true', {});
            const msg = '✓ Debug mode enabled.\n\nServer logging increased to DEBUG level.';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
            console.log('[Debug Mode] Enabled');
          } else if (mode === 'off') {
            await apiClient.post('/debug/toggle?enabled=false', {});
            const msg = '✓ Debug mode disabled.\n\nServer logging set to normal level.';
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
            console.log('[Debug Mode] Disabled');
          } else if (mode === 'status' || mode === '') {
            const response = await apiClient.get<{ debug_enabled: boolean }>('/debug/status');
            const status = response.debug_enabled ? 'ON' : 'OFF';
            const msg = `Debug mode is currently: ${status}\n\nUsage: /debug on|off|status`;
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
            console.log('[Debug Mode] Status:', status);
          } else {
            const msg = `Unknown debug command: ${mode}\n\nUsage: /debug on|off|status`;
            setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
          }
        } catch (error) {
          console.error('[Debug] Error:', error);
          const msg = '❌ Failed to toggle debug mode. Please check your connection and permissions.';
          setMessages(prev => [...prev, { role: 'assistant', content: msg, type: 'command' }]);
        }
        return;
      }

      // For navigation commands, show executing message and call callback
      console.log('[NLUWidget] Executing navigation command:', userInput);
      const executingMsg = `Executing: ${userInput}`;
      setMessages(prev => [...prev, { role: 'assistant', content: executingMsg, type: 'command' }]);

      // Call the command handler with a small delay to ensure message renders first
      setTimeout(() => {
        console.log('[NLUWidget] Calling onCommandExecute with:', userInput);
        onCommandExecute?.(userInput);
      }, 100);
      return;
    }

    // For natural language, use free_session API for conversational response
    setIsLoading(true);
    try {
      const response = await freeSessionAPI.ask(userInput, sessionId);

      // Display the conversational response
      setMessages(prev => [...prev, { role: 'assistant', content: response.answer, type: 'message' }]);

      // If there are suggested commands, show them
      if (response.suggested_commands && response.suggested_commands.length > 0) {
        const suggestionsMsg = `\nYou can also try:\n${response.suggested_commands.slice(0, 3).map(cmd => `• ${cmd}`).join('\n')}`;
        setMessages(prev => [...prev, { role: 'assistant', content: suggestionsMsg, type: 'suggestion' }]);
      }
    } catch (error) {
      console.error('Free session error:', error);
      // Fallback to NLU interpret for command suggestions
      try {
        const result = await nluAPI.interpret(userInput, context);

        if (result.status === 'success' && result.command) {
          const responseMsg = `🎯 Understood! Executing: ${result.command}`;
          setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'command' }]);
          onCommandExecute?.(result.command);
        } else if (result.status === 'suggestions' && result.suggestions && result.suggestions.length > 0) {
          const suggestionText = result.suggestions
            .slice(0, 3)
            .map((s, i) => `${i + 1}. ${s.command} (${Math.round(s.confidence * 100)}%)`)
            .join('\n');
          const responseMsg = `Did you mean?\n${suggestionText}`;
          setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'suggestion' }]);
        } else {
          const responseMsg = result.message || "I'm not sure how to help with that. Try typing /help for available commands.";
          setMessages(prev => [...prev, { role: 'assistant', content: responseMsg, type: 'message' }]);
        }
      } catch (fallbackError) {
        console.error('Fallback NLU error:', fallbackError);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          type: 'message'
        }]);
      }
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
                className={`max-w-md lg:max-w-xl px-3 py-2 rounded-lg text-sm ${
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
