/**
 * EmptyState Component - Display when no files exist
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion, ArrowRight } from 'lucide-react';

export const EmptyState: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[500px] bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
      <div className="text-center px-6 py-12 max-w-md">
        <FileQuestion className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          No files generated yet
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Start by generating code using the Code Generation feature. Generated files will appear here.
        </p>
        <Link
          to="/code-generation"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors font-medium"
        >
          Go to Code Generation
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};

export default EmptyState;
