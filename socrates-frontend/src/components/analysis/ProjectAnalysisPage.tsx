/**
 * ProjectAnalysisPage - Project analysis display
 */

import React from 'react';

interface ProjectAnalysisPageProps {
  projectId: string;
}

export const ProjectAnalysisPage: React.FC<ProjectAnalysisPageProps> = ({ projectId }) => {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
        Project Analysis
      </h2>
      <p className="text-gray-600 dark:text-gray-400 mb-4">
        Analysis details for project: {projectId}
      </p>
      <p className="text-gray-600 dark:text-gray-400">
        This feature is under development.
      </p>
    </div>
  );
};

export default ProjectAnalysisPage;
