/**
 * ComingSoon Component - Feature not yet available
 */

import React from 'react';
import { Sparkles } from 'lucide-react';

interface ComingSoonProps {
  title?: string;
  description?: string;
  releaseDate?: string;
}

export const ComingSoon: React.FC<ComingSoonProps> = ({
  title = 'Coming Soon',
  description = 'This feature is currently in development and will be available soon.',
  releaseDate,
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="mb-4">
        <Sparkles size={48} className="text-yellow-500 dark:text-yellow-400 animate-pulse" />
      </div>
      <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-gray-600 dark:text-gray-400 text-center max-w-md mb-4">
        {description}
      </p>
      {releaseDate && (
        <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
          Expected: {releaseDate}
        </p>
      )}
    </div>
  );
};

ComingSoon.displayName = 'ComingSoon';
