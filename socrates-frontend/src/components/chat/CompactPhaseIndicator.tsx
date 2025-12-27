/**
 * CompactPhaseIndicator - Phase progress indicator with dots
 * Shows 4 dots representing project phases
 */

import React from 'react';
import { Tooltip } from '../common';

interface Phase {
  number: number;
  name: string;
  isComplete: boolean;
  isCurrent: boolean;
}

interface CompactPhaseIndicatorProps {
  currentPhase: number; // 1-4
  phases: Phase[];
  onPhaseClick?: (phaseNumber: number) => void;
}

export const CompactPhaseIndicator: React.FC<CompactPhaseIndicatorProps> = ({
  currentPhase,
  phases,
  onPhaseClick,
}) => {
  const getPhaseColor = (phase: Phase) => {
    if (phase.isCurrent) {
      return 'bg-blue-600 dark:bg-blue-500'; // Current - filled blue
    }
    if (phase.isComplete) {
      return 'bg-green-600 dark:bg-green-500'; // Complete - filled green
    }
    return 'bg-gray-300 dark:bg-gray-600'; // Future - empty gray
  };

  const getPhaseRing = (phase: Phase) => {
    if (phase.isCurrent) {
      return 'ring-2 ring-blue-400 dark:ring-blue-300'; // Current - blue ring
    }
    return '';
  };

  return (
    <div className="flex items-center gap-2">
      {phases.map((phase) => (
        <Tooltip
          key={phase.number}
          content={phase.name}
          side="bottom"
        >
          <button
            onClick={() => onPhaseClick?.(phase.number)}
            disabled={!onPhaseClick}
            className={`
              w-3 h-3 rounded-full transition-all
              ${getPhaseColor(phase)}
              ${getPhaseRing(phase)}
              ${onPhaseClick ? 'cursor-pointer hover:scale-125' : 'cursor-default'}
            `}
            title={`Phase ${phase.number}: ${phase.name}`}
          />
        </Tooltip>
      ))}
    </div>
  );
};

CompactPhaseIndicator.displayName = 'CompactPhaseIndicator';
