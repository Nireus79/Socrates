/**
 * QuestionDisplay Component - Render current Socratic question
 */

import React from 'react';
import { Card, Badge } from '../common';

interface QuestionDisplayProps {
  questionNumber: number;
  totalQuestions: number;
  category: string;
  question: string;
  context?: string;
  hints?: string[];
}

export const QuestionDisplay: React.FC<QuestionDisplayProps> = ({
  questionNumber,
  totalQuestions,
  category,
  question,
  context,
  hints,
}) => {
  return (
    <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900 dark:to-indigo-900">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex justify-between items-start gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="primary">Question {questionNumber}/{totalQuestions}</Badge>
              <Badge variant="secondary">{category}</Badge>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-400">
              Progress: {Math.round((questionNumber / totalQuestions) * 100)}%
            </p>
          </div>
          <div className="h-8 w-8 rounded-full bg-blue-200 dark:bg-blue-700 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-bold text-blue-900 dark:text-blue-100">
              {questionNumber}
            </span>
          </div>
        </div>

        {/* Question */}
        <div className="border-t border-blue-200 dark:border-blue-700 pt-4">
          <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {question}
          </p>
          {context && (
            <p className="text-sm text-gray-700 dark:text-gray-300 mt-3">
              <span className="font-medium">Context:</span> {context}
            </p>
          )}
        </div>

        {/* Hints */}
        {hints && hints.length > 0 && (
          <div className="border-t border-blue-200 dark:border-blue-700 pt-4">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
              Available Hints ({hints.length})
            </p>
            <div className="space-y-2">
              {hints.map((hint, index) => (
                <details key={index} className="cursor-pointer">
                  <summary className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                    Hint {index + 1}
                  </summary>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-2 ml-4">
                    {hint}
                  </p>
                </details>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

QuestionDisplay.displayName = 'QuestionDisplay';
