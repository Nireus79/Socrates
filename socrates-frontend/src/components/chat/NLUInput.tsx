/**
 * NLUInput Component - Natural Language Understanding chat interface
 * Allows users to give commands in natural language with confirmation
 */

import React, { useState } from 'react';
import { Send, Lightbulb, AlertCircle, CheckCircle, XCircle, Wand2 } from 'lucide-react';
import { TextArea, Button } from '../common';
import { chatAPI } from '../../api';

interface NLUInputProps {
  projectId: string;
  isLoading?: boolean;
  onCommandConfirmed?: (command: string) => void;
  placeholder?: string;
}

interface CommandSuggestion {
  command: string;
  reasoning: string;
  confidence: number;
  entities?: {
    action?: string;
    object?: string;
    parameters?: string[];
    intent_category?: string;
  };
}

export const NLUInput: React.FC<NLUInputProps> = ({
  projectId,
  isLoading = false,
  onCommandConfirmed,
  placeholder = 'Ask me anything or give me a command... (e.g., "Create a project named X" or "Show hints")',
}) => {
  const [input, setInput] = useState('');
  const [isInterpreting, setIsInterpreting] = useState(false);
  const [suggestions, setSuggestions] = useState<CommandSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<CommandSuggestion | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [interpretationMessage, setInterpretationMessage] = useState<string>('');

  const handleInterpret = async () => {
    if (!input.trim()) return;

    setIsInterpreting(true);
    setError(null);
    setSuggestions([]);
    setSelectedSuggestion(null);
    setInterpretationMessage('');

    try {
      const response = await chatAPI.interpretNLU(projectId, input);

      if (response.status === 'no_match') {
        setError('I didn\'t understand that. Could you rephrase or try a slash command like /help?');
        setIsInterpreting(false);
        return;
      }

      if (response.status === 'suggestions' && response.data?.suggestions) {
        setSuggestions(response.data.suggestions);
        setInterpretationMessage('I found a few possibilities. Which one did you mean?');
        setIsInterpreting(false);
        return;
      }

      if (response.data?.command) {
        const suggestion: CommandSuggestion = {
          command: response.data.command,
          reasoning: response.data.entities?.intent_category
            ? `Detected: ${response.data.entities.intent_category}`
            : 'I understood your request',
          confidence: response.data.entities?.confidence || 1.0,
          entities: response.data.entities,
        };

        setSelectedSuggestion(suggestion);
        setShowConfirmation(true);
        setInterpretationMessage(`I interpreted this as: "${suggestion.command}"`);
      }

      setIsInterpreting(false);
    } catch (err) {
      setError('Failed to interpret your request. Please try again.');
      setIsInterpreting(false);
    }
  };

  const handleSelectSuggestion = (suggestion: CommandSuggestion) => {
    setSelectedSuggestion(suggestion);
    setShowConfirmation(true);
    setInterpretationMessage(`I interpreted this as: "${suggestion.command}"`);
  };

  const handleConfirmCommand = () => {
    if (selectedSuggestion && onCommandConfirmed) {
      onCommandConfirmed(selectedSuggestion.command);
      setInput('');
      setSuggestions([]);
      setSelectedSuggestion(null);
      setShowConfirmation(false);
      setInterpretationMessage('');
    }
  };

  const handleReject = () => {
    setShowConfirmation(false);
    setSelectedSuggestion(null);
    setSuggestions([]);
    setInterpretationMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (input.trim() && !isInterpreting) {
        handleInterpret();
      }
    }
  };

  return (
    <div className="space-y-3 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
      {/* Header */}
      <div className="flex items-center gap-2 text-sm font-medium text-purple-700 dark:text-purple-300">
        <Wand2 className="h-4 w-4" />
        Natural Language Commands
      </div>

      {/* Input Area */}
      <TextArea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={3}
        disabled={isInterpreting || isLoading}
        className="resize-none"
      />

      {/* Interpretation Message */}
      {interpretationMessage && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded text-sm text-blue-700 dark:text-blue-300 flex items-start gap-2">
          <Lightbulb className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{interpretationMessage}</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded text-sm text-red-700 dark:text-red-300 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Suggestions List */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="w-full p-3 text-left bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded hover:border-purple-400 dark:hover:border-purple-600 transition"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="font-mono text-sm text-purple-600 dark:text-purple-400">
                    {suggestion.command}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {suggestion.reasoning}
                  </div>
                </div>
                <div className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 px-2 py-1 rounded whitespace-nowrap">
                  {Math.round(suggestion.confidence * 100)}%
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Confirmation Section */}
      {showConfirmation && selectedSuggestion && (
        <div className="p-4 bg-green-50 dark:bg-green-900/30 border-2 border-green-200 dark:border-green-700 rounded space-y-3">
          <div className="flex items-start gap-2">
            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
            <div>
              <div className="font-medium text-green-900 dark:text-green-100">
                Ready to execute this command?
              </div>
              <div className="font-mono text-sm text-green-700 dark:text-green-300 mt-1 p-2 bg-green-100 dark:bg-green-900/50 rounded">
                {selectedSuggestion.command}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="primary"
              icon={<CheckCircle className="h-4 w-4" />}
              onClick={handleConfirmCommand}
              disabled={isLoading}
            >
              Yes, execute
            </Button>
            <Button
              variant="secondary"
              icon={<XCircle className="h-4 w-4" />}
              onClick={handleReject}
              disabled={isLoading}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Send Button */}
      {!showConfirmation && (
        <div className="flex gap-2">
          <Button
            variant="primary"
            icon={<Send className="h-4 w-4" />}
            onClick={handleInterpret}
            disabled={!input.trim() || isInterpreting || isLoading}
            isLoading={isInterpreting}
            fullWidth
          >
            {isInterpreting ? 'Interpreting...' : 'Interpret'}
          </Button>
        </div>
      )}
    </div>
  );
};
