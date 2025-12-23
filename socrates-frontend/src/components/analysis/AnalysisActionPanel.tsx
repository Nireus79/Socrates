/**
 * Analysis Action Panel - Buttons for running different analyses
 */

import React from 'react';
import {
  CheckCircle,
  AlertCircle,
  FileText,
  Zap,
  Wrench,
} from 'lucide-react';
import { useAnalysisStore } from '../../stores';
import { Card } from '../common';
import { Button } from '../common';

interface AnalysisActionPanelProps {
  projectId: string;
}

export const AnalysisActionPanel: React.FC<AnalysisActionPanelProps> = ({
  projectId,
}) => {
  const {
    isValidating,
    isTesting,
    isAnalyzing,
    isReviewing,
    validateCode,
    runTests,
    analyzeStructure,
    reviewCode,
  } = useAnalysisStore();

  const actions = [
    {
      icon: <AlertCircle className="h-5 w-5" />,
      label: 'Validate Code',
      description: 'Check for syntax and style issues',
      onClick: () => validateCode(projectId),
      isLoading: isValidating,
    },
    {
      icon: <CheckCircle className="h-5 w-5" />,
      label: 'Run Tests',
      description: 'Execute project tests',
      onClick: () => runTests(projectId),
      isLoading: isTesting,
    },
    {
      icon: <FileText className="h-5 w-5" />,
      label: 'Analyze Structure',
      description: 'Review code architecture',
      onClick: () => analyzeStructure(projectId),
      isLoading: isAnalyzing,
    },
    {
      icon: <Zap className="h-5 w-5" />,
      label: 'Code Review',
      description: 'Perform comprehensive review',
      onClick: () => reviewCode(projectId),
      isLoading: isReviewing,
    },
  ];

  return (
    <Card>
      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Analysis Tools
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {actions.map((action) => (
            <Button
              key={action.label}
              variant="secondary"
              fullWidth
              icon={action.icon}
              onClick={action.onClick}
              disabled={action.isLoading}
              isLoading={action.isLoading}
              title={action.description}
            >
              {action.label}
            </Button>
          ))}
        </div>
      </div>
    </Card>
  );
};
