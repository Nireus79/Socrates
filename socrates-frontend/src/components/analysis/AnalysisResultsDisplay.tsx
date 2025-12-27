/**
 * AnalysisResultsDisplay - Display analysis results
 */

import React from 'react';
import { AlertCircle, CheckCircle, AlertTriangle, Info, Loader } from 'lucide-react';
import { Alert } from '../common';

interface AnalysisResultsDisplayProps {
  title: string;
  result: any | null;
  isLoading?: boolean;
  error?: string;
}

export const AnalysisResultsDisplay: React.FC<AnalysisResultsDisplayProps> = ({
  title,
  result,
  isLoading = false,
  error,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="h-8 w-8 text-gray-400 dark:text-gray-600 animate-spin mr-3" />
        <p className="text-gray-600 dark:text-gray-400">Loading {title}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        title="Error"
        description={error}
        variant="error"
      />
    );
  }

  if (!result) {
    return (
      <Alert
        title="No Results"
        description={`No ${title} data available. Run an analysis to generate results.`}
        variant="info"
      />
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {title}
      </h3>

      {/* Status */}
      {result.status && (
        <div className="mb-4 p-3 rounded bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <p className="text-sm">
            <span className="font-medium">Status:</span> {result.status}
          </p>
        </div>
      )}

      {/* Message */}
      {result.message && (
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          {result.message}
        </p>
      )}

      {/* Results as JSON for now */}
      <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-x-auto text-xs text-gray-800 dark:text-gray-200">
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
};
