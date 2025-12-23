/**
 * ResponseInput Component - Text area for user response with action buttons
 */

import React from 'react';
import { Send, SkipForward, Lightbulb } from 'lucide-react';
import { TextArea, Button } from '../common';

interface ResponseInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onSkip?: () => void;
  onRequestHint?: () => void;
  isLoading?: boolean;
  minLength?: number;
  maxLength?: number;
  placeholder?: string;
}

export const ResponseInput: React.FC<ResponseInputProps> = ({
  value,
  onChange,
  onSubmit,
  onSkip,
  onRequestHint,
  isLoading = false,
  minLength = 1,
  maxLength = 5000,
  placeholder = 'Type your response...',
}) => {
  const isValid = value.trim().length >= minLength && value.length <= maxLength;
  const charCount = value.length;

  return (
    <div className="space-y-3">
      {/* Text Input */}
      <TextArea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={4}
        disabled={isLoading}
        maxLength={maxLength}
        className="resize-none"
      />

      {/* Character Count */}
      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-400">
        <span>
          {charCount} / {maxLength} characters
        </span>
        {charCount >= maxLength * 0.9 && (
          <span className="text-orange-600 dark:text-orange-400">
            Approaching limit
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <Button
          variant="primary"
          icon={<Send className="h-4 w-4" />}
          onClick={onSubmit}
          disabled={!isValid || isLoading}
          fullWidth
          isLoading={isLoading}
        >
          {isLoading ? 'Submitting...' : 'Submit Response'}
        </Button>

        {onRequestHint && (
          <Button
            variant="secondary"
            icon={<Lightbulb className="h-4 w-4" />}
            onClick={onRequestHint}
            disabled={isLoading}
            title="Request a hint for this question"
          >
            Hint
          </Button>
        )}

        {onSkip && (
          <Button
            variant="ghost"
            icon={<SkipForward className="h-4 w-4" />}
            onClick={onSkip}
            disabled={isLoading}
            title="Skip this question"
          >
            Skip
          </Button>
        )}
      </div>
    </div>
  );
};

ResponseInput.displayName = 'ResponseInput';
