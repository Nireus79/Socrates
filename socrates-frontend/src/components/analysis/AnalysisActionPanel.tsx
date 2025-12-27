/**
 * AnalysisActionPanel - Action buttons for project analysis
 */

import React from 'react';
import { CheckCircle, Bug, ThumbsUp, TrendingUp, Layers, Wand2, FileText } from 'lucide-react';
import { Button } from '../common';

interface AnalysisActionPanelProps {
  projectId: string;
  isLoading?: boolean;
  onValidate: () => void;
  onTest: () => void;
  onReview: () => void;
  onMaturity: () => void;
  onStructure: () => void;
  onFix: () => void;
  onReport: () => void;
}

export const AnalysisActionPanel: React.FC<AnalysisActionPanelProps> = ({
  projectId,
  isLoading = false,
  onValidate,
  onTest,
  onReview,
  onMaturity,
  onStructure,
  onFix,
  onReport,
}) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Analysis Actions
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Validate Button */}
        <Button
          variant="secondary"
          icon={<CheckCircle className="h-4 w-4" />}
          onClick={onValidate}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Validate Code
        </Button>

        {/* Test Button */}
        <Button
          variant="secondary"
          icon={<Bug className="h-4 w-4" />}
          onClick={onTest}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Run Tests
        </Button>

        {/* Review Button */}
        <Button
          variant="secondary"
          icon={<ThumbsUp className="h-4 w-4" />}
          onClick={onReview}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Code Review
        </Button>

        {/* Maturity Button */}
        <Button
          variant="secondary"
          icon={<TrendingUp className="h-4 w-4" />}
          onClick={onMaturity}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Assess Maturity
        </Button>

        {/* Structure Button */}
        <Button
          variant="secondary"
          icon={<Layers className="h-4 w-4" />}
          onClick={onStructure}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Analyze Structure
        </Button>

        {/* Fix Button */}
        <Button
          variant="secondary"
          icon={<Wand2 className="h-4 w-4" />}
          onClick={onFix}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          Fix Issues
        </Button>

        {/* Report Button */}
        <Button
          variant="secondary"
          icon={<FileText className="h-4 w-4" />}
          onClick={onReport}
          disabled={isLoading || !projectId}
          className="justify-center"
        >
          View Report
        </Button>
      </div>

      {!projectId && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
          Select a project to enable analysis actions
        </p>
      )}
    </div>
  );
};
