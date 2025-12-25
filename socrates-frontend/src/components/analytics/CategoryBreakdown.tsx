/**
 * CategoryBreakdown Component - Show all categories with progress
 */

import React from 'react';
import { Card, Progress, Badge } from '../common';

interface Category {
  name: string;
  maturity: number;
  confidence: number;
  specCount: number;
}

interface CategoryBreakdownProps {
  phase: number;
  categories: Category[];
}

export const CategoryBreakdown: React.FC<CategoryBreakdownProps> = ({
  phase,
  categories,
}) => {
  const phaseNames = ['Discovery', 'Analysis', 'Design', 'Implementation'];

  return (
    <Card>
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {phaseNames[phase - 1]} Categories
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Progress across all {categories.length} categories for this phase
          </p>
        </div>

        <div className="space-y-3">
          {categories.map((category) => (
            <div key={category.name} className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    {category.name}
                  </h4>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" size="sm">
                      {category.specCount} spec{category.specCount !== 1 ? 's' : ''}
                    </Badge>
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {category.confidence}% confident
                    </span>
                  </div>
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white flex-shrink-0">
                  {category.maturity}%
                </span>
              </div>

              <Progress value={category.maturity} size="sm" />
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="grid grid-cols-3 gap-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <p className="text-xs text-gray-600 dark:text-gray-400">Average</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white">
              {Math.round(
                categories.reduce((sum, cat) => sum + cat.maturity, 0) / categories.length
              )}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-600 dark:text-gray-400">Strongest</p>
            <p className="text-lg font-bold text-green-600 dark:text-green-400">
              {Math.max(...categories.map((c) => c.maturity))}%
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-600 dark:text-gray-400">Weakest</p>
            <p className="text-lg font-bold text-orange-600 dark:text-orange-400">
              {Math.min(...categories.map((c) => c.maturity))}%
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
};

CategoryBreakdown.displayName = 'CategoryBreakdown';
