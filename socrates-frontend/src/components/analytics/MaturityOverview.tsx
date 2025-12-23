/**
 * MaturityOverview Component - Overall maturity score and phase breakdown
 */

import React from 'react';
import { TrendingUp, Lock, CheckCircle } from 'lucide-react';
import { Card, Badge, Progress } from '../common';

interface PhaseMaturity {
  number: number;
  name: string;
  maturity: number;
  isComplete: boolean;
}

interface MaturityOverviewProps {
  overallMaturity: number;
  phases: PhaseMaturity[];
  strongestCategory?: string;
  weakestCategory?: string;
  readyToAdvance?: boolean;
}

export const MaturityOverview: React.FC<MaturityOverviewProps> = ({
  overallMaturity,
  phases,
  strongestCategory,
  weakestCategory,
  readyToAdvance,
}) => {
  const phaseColors = ['from-blue-500', 'from-purple-500', 'from-pink-500', 'from-green-500'];

  return (
    <div className="space-y-6">
      {/* Overall Maturity Circle */}
      <Card>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-8">
          {/* Circular Progress */}
          <div className="flex-shrink-0">
            <div className="relative w-40 h-40">
              {/* Background circle */}
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="8"
                  className="text-gray-200 dark:text-gray-700"
                />
                {/* Progress circle */}
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="url(#gradient)"
                  strokeWidth="8"
                  strokeDasharray={`${overallMaturity * 2.83} 283`}
                  strokeLinecap="round"
                  className="transition-all duration-500"
                />
                <defs>
                  <linearGradient
                    id="gradient"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop offset="0%" stopColor="rgb(59, 130, 246)" />
                    <stop offset="100%" stopColor="rgb(139, 92, 246)" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Center text */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-4xl font-bold text-gray-900 dark:text-white">
                    {overallMaturity}%
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Overall
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Info Section */}
          <div className="flex-1 space-y-4">
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project Status
              </p>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {overallMaturity < 25
                    ? 'Just Getting Started'
                    : overallMaturity < 50
                    ? 'Making Progress'
                    : overallMaturity < 75
                    ? 'Nearly There'
                    : 'Ready for Production'}
                </p>
              </div>
            </div>

            {strongestCategory && (
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Strongest Area
                </p>
                <Badge variant="success">{strongestCategory}</Badge>
              </div>
            )}

            {weakestCategory && (
              <div>
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Needs Focus
                </p>
                <Badge variant="warning">{weakestCategory}</Badge>
              </div>
            )}

            {readyToAdvance && (
              <div className="p-3 bg-green-50 dark:bg-green-900 rounded-lg border border-green-200 dark:border-green-700">
                <p className="text-sm font-medium text-green-900 dark:text-green-100">
                  ✓ Ready to advance to next phase!
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Phase Breakdown */}
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Phase Maturity
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {phases.map((phase, index) => (
            <div key={phase.number} className="space-y-2">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className={`w-8 h-8 rounded-full bg-gradient-to-br ${phaseColors[index]} flex items-center justify-center text-white text-sm font-bold`}
                >
                  {phase.number}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {phase.name}
                  </p>
                  {phase.isComplete && (
                    <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-1" />
                  )}
                </div>
              </div>

              <div className="flex justify-between items-center mb-1">
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Maturity
                </span>
                <span className="text-sm font-semibold text-gray-900 dark:text-white">
                  {phase.maturity}%
                </span>
              </div>

              <Progress
                value={phase.maturity}
                size="sm"
                variant={
                  phase.maturity >= 80
                    ? 'success'
                    : phase.maturity >= 60
                    ? 'warning'
                    : 'primary'
                }
              />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

MaturityOverview.displayName = 'MaturityOverview';
