import React from 'react';
import { Modal } from '../common/dialog/Modal';
import { Button } from '../common/interactive/Button';
import { Lightbulb } from 'lucide-react';

interface AnswerSuggestionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  suggestions: string[];
  question: string;
  phase: string;
  onSelectSuggestion: (suggestion: string) => void;
}

export const AnswerSuggestionsModal: React.FC<AnswerSuggestionsModalProps> = ({
  isOpen,
  onClose,
  suggestions,
  question,
  phase,
  onSelectSuggestion,
}) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Answer Suggestions" size="lg">
      <div className="space-y-4">
        {/* Header with question context */}
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-slate-600 dark:text-slate-300 mb-2 font-medium">
            Current Question ({phase} phase):
          </p>
          <p className="text-base text-slate-800 dark:text-slate-100 italic">
            "{question}"
          </p>
        </div>

        {/* Suggestions */}
        <div>
          <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">
            Suggested answer starters:
          </p>
          <div className="space-y-2">
            {suggestions.map((suggestion, index) => (
              <div
                key={index}
                className="p-3 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition cursor-pointer"
                onClick={() => {
                  onSelectSuggestion(suggestion);
                  onClose();
                }}
              >
                <div className="flex items-start gap-3">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400 mt-0.5">
                    {index + 1}
                  </span>
                  <p className="text-sm text-slate-700 dark:text-slate-300">{suggestion}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-700">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
          <Button variant="primary" onClick={onClose}>
            Done
          </Button>
        </div>

        {/* Hint */}
        <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
          Click any suggestion to use it as your answer starter
        </p>
      </div>
    </Modal>
  );
};
