/**
 * Analysis Results Display - Show analysis results
 */

import React from 'react';
import { RefreshCw, Loader, AlertCircle, CheckCircle } from 'lucide-react';
import { Card } from '../common';
import { Button } from '../common';
import { Badge } from '../common';

interface AnalysisResultsDisplayProps {
  title: string;
  icon: React.ReactNode;
  isLoading: boolean;
  onRefresh: () => void;
  results: any;
  resultType: 'validation' | 'tests' | 'structure' | 'review';
}

export const AnalysisResultsDisplay: React.FC<
  AnalysisResultsDisplayProps
> = ({
  title,
  icon,
  isLoading,
  onRefresh,
  results,
  resultType,
}) => {
  if (isLoading) {
    return (
      <Card className="text-center py-12">
        <Loader className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-4 animate-spin" />
        <p className="text-gray-600 dark:text-gray-400">Loading results...</p>
      </Card>
    );
  }

  if (!results) {
    return (
      <Card className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          No {title.toLowerCase()} results yet
        </p>
        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw className="h-4 w-4" />}
          onClick={onRefresh}
        >
          Run {title}
        </Button>
      </Card>
    );
  }

  return (
    <Card>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-blue-600 dark:text-blue-400">{icon}</div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              {title} Results
            </h2>
          </div>
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="h-4 w-4" />}
            onClick={onRefresh}
          >
            Refresh
          </Button>
        </div>

        {/* Results Summary */}
        {resultType === 'validation' && results && (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Valid Files
                </p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {results.valid_files}/{results.total_files}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Issues
                </p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {results.files_with_issues}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Quality Score
                </p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {results.code_quality_score}%
                </p>
              </div>
            </div>
          </div>
        )}

        {resultType === 'tests' && results && (
          <div className="space-y-3">
            <div className="grid grid-cols-4 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Total
                </p>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {results.total_tests}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Passed
                </p>
                <p className="text-xl font-bold text-green-600 dark:text-green-400">
                  {results.passed}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Failed
                </p>
                <p className="text-xl font-bold text-red-600 dark:text-red-400">
                  {results.failed}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Coverage
                </p>
                <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                  {results.coverage}%
                </p>
              </div>
            </div>
          </div>
        )}

        {resultType === 'structure' && results && (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Files
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {results.files}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Complexity
                </p>
                <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {results.complexity_score}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Maintainability
                </p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {results.maintainability_index}
                </p>
              </div>
            </div>
            <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
              <p className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">
                Total Lines of Code
              </p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {results.total_lines.toLocaleString()}
              </p>
            </div>
          </div>
        )}

        {resultType === 'review' && results && (
          <div className="space-y-3">
            <div className="grid grid-cols-4 gap-3">
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Critical
                </p>
                <p className="text-xl font-bold text-red-600 dark:text-red-400">
                  {results.critical}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Major
                </p>
                <p className="text-xl font-bold text-orange-600 dark:text-orange-400">
                  {results.major}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Minor
                </p>
                <p className="text-xl font-bold text-yellow-600 dark:text-yellow-400">
                  {results.minor}
                </p>
              </div>
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Suggestions
                </p>
                <p className="text-xl font-bold text-blue-600 dark:text-blue-400">
                  {results.suggestions}
                </p>
              </div>
            </div>
            <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-md border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {results.summary}
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
