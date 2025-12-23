/**
 * CodeValidation Component - Display validation results and code metrics
 */

import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, Code2 } from 'lucide-react';
import { Card, Badge } from '../common';

export interface ValidationIssue {
  id: string;
  type: 'error' | 'warning' | 'suggestion';
  line?: number;
  message: string;
}

export interface CodeMetrics {
  complexity: number; // 1-10
  readability: number; // 0-100
  documentation: number; // 0-100
  testCoverage: number; // 0-100
}

interface CodeValidationProps {
  issues: ValidationIssue[];
  metrics: CodeMetrics;
  isLoading?: boolean;
}

export const CodeValidation: React.FC<CodeValidationProps> = ({
  issues,
  metrics,
  isLoading = false,
}) => {
  const errorCount = issues.filter((i) => i.type === 'error').length;
  const warningCount = issues.filter((i) => i.type === 'warning').length;
  const suggestionCount = issues.filter((i) => i.type === 'suggestion').length;

  const getMetricColor = (value: number, isLow = false): string => {
    if (isLow) {
      // For metrics where lower is better (complexity)
      if (value <= 3) return 'text-green-600 dark:text-green-400';
      if (value <= 7) return 'text-yellow-600 dark:text-yellow-400';
      return 'text-red-600 dark:text-red-400';
    }
    // For metrics where higher is better (readability, docs, tests)
    if (value >= 80) return 'text-green-600 dark:text-green-400';
    if (value >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getIssueIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />;
      case 'suggestion':
        return <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />;
      default:
        return <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card>
        <div className="flex gap-4 flex-wrap">
          <div className="flex-1 min-w-[120px]">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Errors
              </span>
            </div>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">
              {errorCount}
            </p>
          </div>

          <div className="flex-1 min-w-[120px]">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Warnings
              </span>
            </div>
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {warningCount}
            </p>
          </div>

          <div className="flex-1 min-w-[120px]">
            <div className="flex items-center gap-2 mb-1">
              <Info className="h-4 w-4 text-blue-600 dark:text-blue-400" />
              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                Suggestions
              </span>
            </div>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {suggestionCount}
            </p>
          </div>
        </div>
      </Card>

      {/* Metrics */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Code Metrics
        </h3>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Complexity
              </span>
              <span
                className={`text-lg font-bold ${getMetricColor(metrics.complexity, true)}`}
              >
                {metrics.complexity}/10
              </span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  metrics.complexity <= 3
                    ? 'bg-green-500'
                    : metrics.complexity <= 7
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${(metrics.complexity / 10) * 100}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Readability
              </span>
              <span className={`text-lg font-bold ${getMetricColor(metrics.readability)}`}>
                {metrics.readability}%
              </span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  metrics.readability >= 80
                    ? 'bg-green-500'
                    : metrics.readability >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${metrics.readability}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Documentation
              </span>
              <span className={`text-lg font-bold ${getMetricColor(metrics.documentation)}`}>
                {metrics.documentation}%
              </span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  metrics.documentation >= 80
                    ? 'bg-green-500'
                    : metrics.documentation >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${metrics.documentation}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Test Coverage
              </span>
              <span className={`text-lg font-bold ${getMetricColor(metrics.testCoverage)}`}>
                {metrics.testCoverage}%
              </span>
            </div>
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  metrics.testCoverage >= 80
                    ? 'bg-green-500'
                    : metrics.testCoverage >= 60
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${metrics.testCoverage}%` }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Issues List */}
      {issues.length > 0 && (
        <Card>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Issues ({issues.length})
          </h3>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className={`p-3 rounded-lg border ${
                  issue.type === 'error'
                    ? 'bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700'
                    : issue.type === 'warning'
                    ? 'bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700'
                    : 'bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700'
                }`}
              >
                <div className="flex gap-3">
                  {getIssueIcon(issue.type)}
                  <div className="flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        issue.type === 'error'
                          ? 'text-red-900 dark:text-red-100'
                          : issue.type === 'warning'
                          ? 'text-yellow-900 dark:text-yellow-100'
                          : 'text-blue-900 dark:text-blue-100'
                      }`}
                    >
                      {issue.message}
                    </p>
                    {issue.line && (
                      <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                        Line {issue.line}
                      </p>
                    )}
                  </div>
                  <Badge
                    variant={
                      issue.type === 'error'
                        ? 'error'
                        : issue.type === 'warning'
                        ? 'warning'
                        : 'info'
                    }
                    size="sm"
                    className="flex-shrink-0"
                  >
                    {issue.type}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {issues.length === 0 && (
        <Card>
          <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
            <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
            <p className="text-sm text-green-900 dark:text-green-100">
              No issues found! Your code looks great.
            </p>
          </div>
        </Card>
      )}
    </div>
  );
};

CodeValidation.displayName = 'CodeValidation';
