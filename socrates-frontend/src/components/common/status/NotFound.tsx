/**
 * NotFound Component - 404 error state
 */

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface NotFoundProps {
  message?: string;
  onNavigate?: () => void;
}

export const NotFound: React.FC<NotFoundProps> = ({
  message = 'The page you are looking for does not exist.',
  onNavigate,
}) => {
  return (
    <div className="flex items-center justify-center min-h-screen px-4">
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <div className="text-8xl font-bold text-gray-200 dark:text-gray-800">
            404
          </div>
        </div>
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
          Page Not Found
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8">{message}</p>
        {onNavigate && (
          <button
            onClick={onNavigate}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 transition-colors"
          >
            Go Back
          </button>
        )}
      </div>
    </div>
  );
};

NotFound.displayName = 'NotFound';
