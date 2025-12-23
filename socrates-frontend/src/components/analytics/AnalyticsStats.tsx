/**
 * AnalyticsStats Component - Key statistics cards
 */

import React from 'react';
import { Card } from '../common';
import { MessageSquare, Code2, Zap, TrendingUp } from 'lucide-react';

interface StatData {
  label: string;
  value: string | number;
  change?: number;
  period?: string;
  icon?: React.ReactNode;
}

interface AnalyticsStatsProps {
  stats: StatData[];
  isLoading?: boolean;
}

export const AnalyticsStats: React.FC<AnalyticsStatsProps> = ({
  stats,
}) => {
  const defaultIcons = {
    'Total Questions': <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />,
    'Code Generated': <Code2 className="h-6 w-6 text-purple-600 dark:text-purple-400" />,
    'Avg Confidence': <Zap className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />,
    'Velocity': <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {stats.map((stat, index) => (
        <Card key={index}>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                {stat.label}
              </p>
              {stat.icon || (defaultIcons[stat.label as keyof typeof defaultIcons] && (
                <div>
                  {defaultIcons[stat.label as keyof typeof defaultIcons]}
                </div>
              ))}
            </div>

            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-bold text-gray-900 dark:text-white">
                {stat.value}
              </p>
              {stat.change !== undefined && (
                <span
                  className={`text-sm font-medium ${
                    stat.change > 0
                      ? 'text-green-600 dark:text-green-400'
                      : stat.change < 0
                      ? 'text-red-600 dark:text-red-400'
                      : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {stat.change > 0 ? '+' : ''}
                  {stat.change}%
                </span>
              )}
            </div>

            {stat.period && (
              <p className="text-xs text-gray-600 dark:text-gray-400">
                {stat.period}
              </p>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};

AnalyticsStats.displayName = 'AnalyticsStats';
