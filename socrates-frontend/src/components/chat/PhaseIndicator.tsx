/**
 * PhaseIndicator Component - Visual indicator of current phase progress
 */

import React from 'react';
import { ChevronRight, Lock } from 'lucide-react';
import { Card, Progress, Button } from '../common';

interface Phase {
  number: number;
  name: string;
  description: string;
  isComplete: boolean;
  isCurrent: boolean;
  isLocked: boolean;
}

interface PhaseIndicatorProps {
  phases: Phase[];
  currentPhase: number;
  maturityByPhase: Record<number, number>;
  onAdvance?: () => void;
  canAdvance?: boolean;
}

const phaseColors = {
  1: 'from-blue-500 to-blue-600',
  2: 'from-purple-500 to-purple-600',
  3: 'from-pink-500 to-pink-600',
  4: 'from-green-500 to-green-600',
};

export const PhaseIndicator: React.FC<PhaseIndicatorProps> = ({
  phases,
  currentPhase,
  maturityByPhase,
  onAdvance,
  canAdvance = false,
}) => {
  return (
    <Card className="space-y-6">
      {/* Phase Timeline */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Project Phases
        </h3>

        <div className="space-y-3">
          {phases.map((phase, index) => {
            const maturity = maturityByPhase[phase.number] || 0;
            const bgColor = phaseColors[phase.number as keyof typeof phaseColors];

            return (
              <div key={phase.number} className="relative">
                {/* Phase Header */}
                <div className="flex items-start gap-3 mb-2">
                  <div
                    className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                      phase.isCurrent
                        ? `bg-gradient-to-r ${bgColor} shadow-lg`
                        : phase.isComplete
                        ? 'bg-green-500'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    {phase.isLocked ? (
                      <Lock className="h-5 w-5" />
                    ) : (
                      phase.number
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                        {phase.name}
                      </h4>
                      {phase.isCurrent && (
                        <span className="text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
                          Current
                        </span>
                      )}
                      {phase.isComplete && (
                        <span className="text-xs font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-0.5 rounded-full">
                          Complete
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {phase.description}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                {!phase.isLocked && (
                  <div className="ml-13 space-y-1">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        Maturity
                      </span>
                      <span className="text-xs font-medium text-gray-900 dark:text-white">
                        {maturity}%
                      </span>
                    </div>
                    <Progress value={maturity} size="sm" />
                  </div>
                )}

                {/* Divider */}
                {index < phases.length - 1 && (
                  <div className="mt-4 ml-5 h-6 border-l-2 border-gray-300 dark:border-gray-600" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Advancement Section */}
      {currentPhase < phases.length && onAdvance && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {canAdvance
              ? 'Phase requirements met. Ready to advance to the next phase?'
              : `Keep answering questions to unlock Phase ${currentPhase + 1}`}
          </p>
          <Button
            variant={canAdvance ? 'primary' : 'secondary'}
            fullWidth
            icon={<ChevronRight className="h-4 w-4" />}
            onClick={onAdvance}
            disabled={!canAdvance}
          >
            {canAdvance ? `Advance to Phase ${currentPhase + 1}` : 'Continue'}
          </Button>
        </div>
      )}
    </Card>
  );
};

PhaseIndicator.displayName = 'PhaseIndicator';
