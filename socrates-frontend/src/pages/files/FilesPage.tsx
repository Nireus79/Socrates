/**
 * Files Page - Browse generated, imported, and saved project files
 *
 * Displays:
 * - Directory structure of generated files
 * - File explorer with syntax highlighting preview
 * - File statistics and metadata
 * - Import/export operations
 */

import React from 'react';
import { useParams } from 'react-router-dom';
import { useProjectStore } from '../../stores/projectStore';

interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  language?: string;
  size?: number;
  children?: FileNode[];
  content?: string;
  createdAt?: string;
  updatedAt?: string;
}

export const FilesPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject } = useProjectStore();

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-8 text-center">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          📁 Project Files
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Browse generated, imported, and saved project files
        </p>

        {projectId && (
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Project: {currentProject?.name || projectId}
            </p>
          </div>
        )}

        <div className="mt-8 text-gray-600 dark:text-gray-400">
          <p className="mb-4">This feature is currently under development.</p>
          <p>The file browser will be available soon.</p>
        </div>
      </div>
    </div>
  );
};

export default FilesPage;
