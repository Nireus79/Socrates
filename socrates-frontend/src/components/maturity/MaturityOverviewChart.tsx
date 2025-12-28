/**
 * MaturityOverviewChart - Display project maturity metrics
 */

import React from 'react';
import { TrendingUp, AlertCircle, CheckCircle } from 'lucide-react';

interface MaturityOverviewChartProps {
  overallScore?: number;
  phaseScores?: Record<string, number>;
  confidenceScore?: number;
  codeQuality?: number;
  isLoading?: boolean;
}

export const MaturityOverviewChart: React.FC<MaturityOverviewChartProps> = ({
  overallScore = 0,
  phaseScores = {},
  confidenceScore = 0,
  codeQuality = 0,
  isLoading = false,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
    if (score >= 60) return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
    if (score >= 40) return 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400';
    return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Needs Improvement';
  };

  const ScoreCircle: React.FC<{ label: string; score: number }> = ({ label, score }) => (
    <div className="flex flex-col items-center">
      <div className={`w-24 h-24 rounded-full flex items-center justify-center ${getScoreColor(score)} font-bold text-lg`}>
        {Math.round(score)}%
      </div>
      <p className="mt-2 text-sm font-medium text-gray-900 dark:text-white">{label}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400">{getScoreLabel(score)}</p>
    </div>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500 dark:text-gray-400">Loading maturity data...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          Project Maturity Overview
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <ScoreCircle label="Overall" score={overallScore} />
          <ScoreCircle label="Confidence" score={confidenceScore} />
          <ScoreCircle label="Code Quality" score={codeQuality} />
        </div>
      </div>

      {/* Phase Scores */}
      {Object.keys(phaseScores).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Phase Maturity Scores
          </h3>

          <div className="space-y-3">
            {Object.entries(phaseScores).map(([phase, score]) => (
              <div key={phase} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                  {phase}
                </span>
                <div className="flex items-center gap-3">
                  <div className="w-40 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getScoreColor(score).split(' ')[0]}`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold text-gray-900 dark:text-white w-12 text-right">
                    {Math.round(score)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
