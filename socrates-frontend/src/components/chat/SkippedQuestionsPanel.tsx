import React, { useState, useEffect } from 'react';
import { useChatStore } from '../../stores/chatStore';
import { Card } from '../common/display/Card';
import { Button } from '../common/interactive/Button';
import { AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface SkippedQuestion {
  id: string;
  question: string;
  phase: string;
  status: string;
  skipped_at: string;
}

interface SkippedQuestionsPanelProps {
  projectId: string;
}

export const SkippedQuestionsPanel: React.FC<SkippedQuestionsPanelProps> = ({ projectId }) => {
  const [skippedQuestions, setSkippedQuestions] = useState<SkippedQuestion[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const getQuestions = useChatStore((state) => state.getQuestions);
  const reopenQuestion = useChatStore((state) => state.reopenQuestion);

  useEffect(() => {
    loadSkippedQuestions();
  }, [projectId]);

  const loadSkippedQuestions = async () => {
    try {
      setIsLoading(true);
      const questions = await getQuestions(projectId, 'skipped');
      setSkippedQuestions(questions);
    } catch (error) {
      console.error('Failed to load skipped questions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReopen = async (questionId: string) => {
    try {
      setIsLoading(true);
      await reopenQuestion(projectId, questionId);
      // Remove from skipped list and reload
      await loadSkippedQuestions();
    } catch (error) {
      console.error('Failed to reopen question:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!skippedQuestions || skippedQuestions.length === 0) {
    return null; // Don't show panel if no skipped questions
  }

  return (
    <Card className="mt-4 p-4 bg-amber-50 dark:bg-amber-900/20 border-l-4 border-amber-500">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <div className="flex items-center gap-2">
          <AlertCircle className="h-5 w-5 text-amber-600" />
          <h3 className="font-semibold text-amber-900 dark:text-amber-100">
            Skipped Questions ({skippedQuestions.length})
          </h3>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5" />
        ) : (
          <ChevronDown className="h-5 w-5" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-3 space-y-2">
          {skippedQuestions.map((question) => (
            <div
              key={question.id}
              className="p-3 bg-white dark:bg-slate-800 rounded border border-amber-200 dark:border-amber-800"
            >
              <p className="text-sm text-slate-700 dark:text-slate-300 mb-2">
                {question.question}
              </p>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span className="text-amber-600 dark:text-amber-400">Phase: {question.phase}</span>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleReopen(question.id)}
                  disabled={isLoading}
                >
                  Answer Now
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
