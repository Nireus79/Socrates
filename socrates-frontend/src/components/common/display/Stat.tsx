/**
 * Stat Component - Single stat display
 */

import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatProps {
  label: string;
  value: string | number;
  change?: {
    value: number;
    direction: 'up' | 'down';
    period: string;
  };
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  change,
  icon,
  trend,
}) => {
  const trendColor =
    trend === 'up'
      ? 'text-green-600 dark:text-green-400'
      : trend === 'down'
      ? 'text-red-600 dark:text-red-400'
      : 'text-gray-600 dark:text-gray-400';

  return (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {label}
        </p>
        <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">
          {value}
        </p>
        {change && (
          <div className={`flex items-center gap-1 mt-2 text-sm ${trendColor}`.trim()}>
            {change.direction === 'up' ? (
              <TrendingUp size={16} />
            ) : (
              <TrendingDown size={16} />
            )}
            <span>
              {change.value}% {change.period}
            </span>
          </div>
        )}
      </div>
      {icon && (
        <div className="text-4xl text-blue-100 dark:text-blue-900/30">
          {icon}
        </div>
      )}
    </div>
  );
};

Stat.displayName = 'Stat';
