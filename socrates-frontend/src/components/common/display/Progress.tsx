/**
 * Progress Component - Progress bar with percentage
 */

import React from 'react';

interface ProgressProps {
  value: number; // 0-100
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  animated?: boolean;
}

const variantColors = {
  primary: 'bg-blue-600 dark:bg-blue-500',
  success: 'bg-green-600 dark:bg-green-500',
  warning: 'bg-yellow-600 dark:bg-yellow-500',
  error: 'bg-red-600 dark:bg-red-500',
};

const sizes = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
};

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'primary',
  showLabel = true,
  animated = true,
}) => {
  const percentage = Math.min(Math.max(value, 0), max) / max * 100;

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden ${sizes[size]}`.trim()}>
        <div
          className={`${variantColors[variant]} ${sizes[size]} rounded-full transition-all duration-500 ${
            animated ? 'animate-pulse' : ''
          }`.trim()}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          {Math.round(percentage)}%
        </p>
      )}
    </div>
  );
};

Progress.displayName = 'Progress';
