/**
 * HintDisplay Component - Modal showing hint for current question
 */

import React from 'react';
import { Lightbulb } from 'lucide-react';
import { Modal, Button } from '../common';

interface HintDisplayProps {
  isOpen: boolean;
  onClose: () => void;
  hint: string;
  questionNumber: number;
}

export const HintDisplay: React.FC<HintDisplayProps> = ({
  isOpen,
  onClose,
  hint,
  questionNumber,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Hint"
      size="sm"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-3 bg-yellow-50 dark:bg-yellow-900 rounded-lg border border-yellow-200 dark:border-yellow-700">
          <Lightbulb className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0" />
          <p className="text-sm text-yellow-900 dark:text-yellow-100">
            Hint for Question {questionNumber}
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
            {hint}
          </p>
        </div>

        <p className="text-xs text-gray-600 dark:text-gray-400">
          Take your time and use this hint to guide your thinking towards the answer.
        </p>

        <Button variant="primary" fullWidth onClick={onClose}>
          Got it
        </Button>
      </div>
    </Modal>
  );
};

HintDisplay.displayName = 'HintDisplay';
