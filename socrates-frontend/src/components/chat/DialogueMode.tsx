/**
 * DialogueMode Component - Toggle between Socratic and Direct modes
 */

import React from 'react';
import { Card, Button } from '../common';
import { MessageCircle, Zap } from 'lucide-react';

type DialogueMode = 'socratic' | 'direct';

interface DialogueModeProps {
  mode: DialogueMode;
  onModeChange: (mode: DialogueMode) => void;
  disabled?: boolean;
  variant?: 'default' | 'compact';
}

export const DialogueMode: React.FC<DialogueModeProps> = ({
  mode,
  onModeChange,
  disabled = false,
  variant = 'default',
}) => {
  // Compact inline toggle variant
  if (variant === 'compact') {
    return (
      <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        <button
          onClick={() => onModeChange('socratic')}
          disabled={disabled}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
            mode === 'socratic'
              ? 'bg-blue-600 text-white'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          title="Socratic Mode"
        >
          Socratic
        </button>
        <button
          onClick={() => onModeChange('direct')}
          disabled={disabled}
          className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
            mode === 'direct'
              ? 'bg-purple-600 text-white'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          title="Direct Mode"
        >
          Direct
        </button>
      </div>
    );
  }

  // Default full card variant
  return (
    <Card>
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Dialogue Mode
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Choose how you'd like to learn and get feedback
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            onClick={() => onModeChange('socratic')}
            disabled={disabled}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'socratic'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <MessageCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 mb-2" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-white">Socratic</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Learn through guided questions and feedback. Great for deep understanding.
              </p>
            </div>
          </button>

          <button
            onClick={() => onModeChange('direct')}
            disabled={disabled}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'direct'
                ? 'border-purple-500 bg-purple-50 dark:bg-purple-900'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400 mb-2" />
            <div className="text-left">
              <p className="font-medium text-gray-900 dark:text-white">Direct</p>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                Get direct answers and explanations. Good for quick learning.
              </p>
            </div>
          </button>
        </div>

        <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-xs font-medium text-gray-900 dark:text-white mb-1">
            {mode === 'socratic' ? 'Socratic Mode Active' : 'Direct Mode Active'}
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400">
            {mode === 'socratic'
              ? 'Claude will ask guiding questions to help you develop your own solutions and understanding.'
              : 'Claude will provide direct answers and explanations to your questions.'}
          </p>
        </div>
      </div>
    </Card>
  );
};

DialogueMode.displayName = 'DialogueMode';
